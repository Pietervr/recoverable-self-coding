"""Bounded review diagnostics on the existing battery unit test's ONE X1 recording.
Reuses its fits, reconstructs fixed decoder coefficients, and computes the exact
conditional readout noise variance from the declared sensor covariance. Eight
additional training-only starts on four folds of one window check optimizer
sensitivity. This does not measure group recovery or run stage C.
"""
import math
import numpy as np
from scipy.special import expit
from sklearn.preprocessing import StandardScaler
import decoder as DEC
import likelihood as LK
import synthetic as SY


def separation(th, x):
    return (np.exp(th[2]) + np.exp(th[3])*expit(np.exp(th[6])*(x-th[4]))) / np.exp(th[1])


def recording_diagnostics(rec, res):
    assert res['status'] == 'ok'
    T = len(rec['time'])
    p, mixing = SY.fixed_pattern_and_mixing()
    env = np.exp(-((rec['time']-SY.ENV_CENTER)**2)/(2*SY.ENV_SD**2))
    baseline = rec['time'] < 0
    covariance = SY.AR_PHI ** np.abs(np.arange(T)[:, None]-np.arange(T)[None, :])
    smooth_impulses = DEC.smooth(np.eye(T))
    samples = DEC.window_samples(rec['time'])
    q = {w: smooth_impulses[:, samples[w]].mean(axis=1) for w in DEC.MAIN}
    trial = rec['trials']
    out = []
    optimizer = []
    for hi, (B, half) in enumerate(sorted(res['decoder']['halves'].items())):
        A = half['decoder_half']
        ra = trial[trial.block.isin(A) & trial.retained & trial.has_epoch]
        Xa = rec['X'][ra.epoch_index.to_numpy()][:, :128, :].astype(np.float64)
        ya = (~ra['catch'].to_numpy(bool)).astype(int)
        coef = np.empty((T, 128))
        offset = np.empty(T)
        for t in range(T):
            sc = StandardScaler().fit(Xa[:, :, t])
            clf = DEC._classifier().fit(sc.transform(Xa[:, :, t]), ya)
            da = clf.decision_function(sc.transform(Xa[:, :, t]))
            mu, sd = da.mean(), da.std(ddof=1)
            assert np.isclose(mu, half['z_mean'][t]) and np.isclose(sd, half['z_sd'][t])
            coef[t] = clf.coef_[0]/sc.scale_/sd
            offset[t] = (clf.intercept_[0] - np.dot(clf.coef_[0]/sc.scale_, sc.mean_) - mu)/sd
        rb = trial[trial.block.isin(B) & trial.retained & trial.has_epoch]
        # Independent reconstruction agrees with the actual decoder on two held-out trials.
        check_X = rec['X'][rb.epoch_index.to_numpy()[:2], :128].astype(float)
        z = np.einsum('nct,tc->nt', check_X, coef) + offset
        check_w = np.stack([DEC.smooth(z)[:, samples[w]].mean(axis=1) for w in DEC.MAIN], axis=1)
        assert np.allclose(check_w, half['W'][:2, DEC.MAIN], rtol=1e-9, atol=1e-9)
        for w in DEC.MAIN:
            C = q[w][:, None]*coef
            Q = C.copy()
            Q[baseline] -= C.sum(axis=0)[None, :]/baseline.sum()
            gain = rec['amplitude']*float(np.einsum('tc,t,c->', Q, env, p))
            projected_sources = Q @ mixing
            noise_variance = float(np.sum(projected_sources*(covariance @ projected_sources)) + SY.SENSOR_SD**2*np.sum(Q*Q))
            effective_sep = 2*abs(gain)/math.sqrt(gain*gain+noise_variance)
            for fi, (btr, bte) in enumerate(((B[0], B[1]), (B[1], B[0]))):
                fit = res['folds'][(hi, fi, w)]['twostate']
                if not fit['available']:
                    continue
                th, sc = fit['theta'], fit['scaling']
                te = half['trials'][(half['trials'].block == bte) & ~half['trials']['catch']]
                x = (np.log(te.contrast.to_numpy(float))-sc['m'])/sc['s']
                full = separation(th, x)
                out.append({'half': list(B), 'train_block': btr, 'test_block': bte, 'window': w,
                            'signal_gain': gain, 'sensor_noise_variance': noise_variance,
                            'true_effective_separation_sd': effective_sep,
                            'fitted_minimum_separation_sd': float(np.exp(th[2]-th[1])),
                            'fitted_total_separation_median_sd': float(np.median(full)),
                            'fitted_total_separation_range_sd': [float(full.min()), float(full.max())],
                            'n_converged': fit['n_converged'], 'n_at_best': fit['n_at_best']})
                if w != 25:
                    continue
                tr = half['trials']
                mask = tr.block.to_numpy() == btr
                catch = tr['catch'].to_numpy(bool)[mask]
                block = LK.Block(half['W'][mask, w], np.where(catch, np.nan, np.log(tr.contrast.to_numpy(float)[mask])),
                                 catch, tr.side.to_numpy()[mask] == 'right')
                d = LK.design(block, sc)
                bounds = LK.bounds('twostate', sc)
                base = LK.moment_start('twostate', d, sc)
                runs = []
                for sigma_fraction in (.5, 1.):
                    for separation_fraction in (.5, 2.):
                        for high_range_fraction in (.01, .5):
                            start = base.copy()
                            start[1] = math.log(sigma_fraction*sc['S'])
                            start[2] = math.log(separation_fraction*sc['S'])
                            start[3] = math.log(high_range_fraction*sc['S'])
                            start[4:7] = (0., math.log(1.5), 0.)
                            runs.append(LK._run('twostate', d, bounds, LK.interior(start, bounds)))
                good = [r for r in runs if r['converged']]
                best = max(good, key=lambda r: r['loglik']) if good else None
                optimizer.append({'train_block': btr, 'test_block': bte, 'window': w, 'n_train': len(block),
                                  'production_train_loglik': fit['loglik'], 'extra_starts': 8, 'extra_converged': len(good),
                                  'best_extra_train_gain_nat': best['loglik']-fit['loglik'] if best else None,
                                  'best_extra_total_separation_median_sd': float(np.median(separation(best['theta'], x))) if best else None})
    fields = ('true_effective_separation_sd', 'fitted_minimum_separation_sd', 'fitted_total_separation_median_sd')
    summary = {k: float(np.median([r[k] for r in out])) for k in fields}
    summary['effective_separation_range_sd'] = [min(r['true_effective_separation_sd'] for r in out), max(r['true_effective_separation_sd'] for r in out)]
    summary['extra_start_max_training_gain_nat'] = max(r['best_extra_train_gain_nat'] for r in optimizer if r['best_extra_train_gain_nat'] is not None)
    return {'scope': 'one existing synthetic test recording; no power estimate', 'generator': rec['generator'], 'amplitude': rec['amplitude'],
            'drift': rec['drift'], 'tags': rec['tags'], 'summary': summary, 'folds': out, 'optimizer_probe': optimizer}
