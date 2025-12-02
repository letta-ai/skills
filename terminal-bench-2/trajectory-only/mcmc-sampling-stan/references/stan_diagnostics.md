# Stan Diagnostics Reference Guide

This reference provides detailed guidance on interpreting and addressing MCMC diagnostic issues in Stan.

## R-hat (Gelman-Rubin Statistic)

### What It Measures
R-hat compares between-chain and within-chain variance. Values near 1.0 indicate chains have converged to the same distribution.

### Thresholds
- **< 1.01**: Good convergence (recommended threshold)
- **1.01 - 1.05**: Marginal; consider running longer
- **> 1.05**: Poor convergence; do not trust results

### Addressing High R-hat
1. Run chains longer (increase `iter`)
2. Check for multimodality in the posterior
3. Consider reparameterization
4. Verify model specification is correct

## Effective Sample Size (ESS)

### What It Measures
ESS estimates the equivalent number of independent samples, accounting for autocorrelation.

### Thresholds
- **> 400**: Reliable for most estimates
- **100 - 400**: Acceptable for initial exploration
- **< 100**: Unreliable; run longer chains

### Types of ESS
- **Bulk ESS**: Reliability of mean and median estimates
- **Tail ESS**: Reliability of tail quantiles (important for credible intervals)

### Addressing Low ESS
1. Increase number of iterations
2. Reparameterize to reduce autocorrelation
3. Consider non-centered parameterization for hierarchical models

## Divergent Transitions

### What They Are
Divergences occur when the Hamiltonian Monte Carlo trajectory diverges due to numerical integration errors, often in regions of high curvature.

### Interpretation
- **Any divergences**: Model has problematic geometry
- **Divergent samples**: May be biased away from high-curvature regions
- **Results unreliable**: Even with few divergences

### Addressing Divergences
1. **Increase `adapt_delta`**: Try 0.95, 0.99, or 0.999
   ```r
   stan(model, data, control = list(adapt_delta = 0.99))
   ```

2. **Reparameterize the model**:
   - Use non-centered parameterization for hierarchical models
   - Transform parameters to have better geometry

3. **Add soft constraints**:
   - Prior bounds that prevent exploration of problematic regions

4. **Check model specification**:
   - Ensure priors are appropriate
   - Verify data is consistent with model

## Tree Depth

### What It Measures
Maximum tree depth limits how far the NUTS sampler can explore in a single step.

### Default and Limits
- Default `max_treedepth`: 10
- Maximum recommended: 15
- Hitting limit consistently indicates inefficiency

### Addressing Tree Depth Warnings
1. Increase `max_treedepth`:
   ```r
   stan(model, data, control = list(max_treedepth = 15))
   ```

2. Consider if model geometry can be improved
3. May indicate model misspecification

## Energy Diagnostics (E-BFMI)

### What It Measures
E-BFMI (Energy Bayesian Fraction of Missing Information) measures how well the sampler explores the energy distribution.

### Thresholds
- **> 0.3**: Acceptable
- **< 0.3**: Poor exploration; may miss regions of posterior

### Addressing Low E-BFMI
1. Reparameterize the model
2. Use stronger priors if appropriate
3. Consider if the model is too complex for the data

## Diagnostic Code Templates

### RStan Complete Diagnostic Check
```r
library(rstan)

# After fitting
fit <- stan(model, data = stan_data, iter = 10000, chains = 4)

# Summary with R-hat and ESS
print(fit)

# Detailed diagnostics
check_hmc_diagnostics(fit)

# Manual divergence check
sampler_params <- get_sampler_params(fit, inc_warmup = FALSE)
n_divergent <- sum(sapply(sampler_params, function(x) sum(x[, "divergent__"])))
cat("Divergent transitions:", n_divergent, "\n")

# Tree depth check
max_td <- 10  # or your setting
n_max_treedepth <- sum(sapply(sampler_params, function(x) sum(x[, "treedepth__"] >= max_td)))
cat("Transitions hitting max treedepth:", n_max_treedepth, "\n")

# Extract specific parameters
alpha_samples <- extract(fit, pars = "alpha")$alpha
mean(alpha_samples)
quantile(alpha_samples, c(0.025, 0.5, 0.975))
```

### PyStan Diagnostic Check
```python
import pystan
import numpy as np

# After fitting
fit = sm.sampling(data=data, iter=10000, chains=4)

# Summary
print(fit)

# Check R-hat
summary = fit.summary()
rhats = summary['summary'][:, -1]  # Last column is R-hat
print(f"Max R-hat: {max(rhats)}")

# Check for divergences (PyStan 2.x)
divergent = fit.get_sampler_params(inc_warmup=False)
n_divergent = sum([sum(x['divergent__']) for x in divergent])
print(f"Divergent transitions: {n_divergent}")
```

## Common Reparameterizations

### Non-Centered Parameterization
For hierarchical models with convergence issues:

**Centered (problematic)**:
```stan
parameters {
  real mu;
  real<lower=0> sigma;
  vector[N] theta;
}
model {
  theta ~ normal(mu, sigma);
}
```

**Non-centered (often better)**:
```stan
parameters {
  real mu;
  real<lower=0> sigma;
  vector[N] theta_raw;
}
transformed parameters {
  vector[N] theta = mu + sigma * theta_raw;
}
model {
  theta_raw ~ std_normal();
}
```

### Log Transformation
For positive parameters with wide range:

```stan
parameters {
  real log_sigma;
}
transformed parameters {
  real<lower=0> sigma = exp(log_sigma);
}
```

## When to Trust Results

Results are trustworthy when ALL of the following are true:
1. R-hat < 1.01 for all parameters
2. Bulk ESS > 400 for all parameters
3. Tail ESS > 400 for all parameters
4. Zero divergent transitions
5. No max treedepth warnings (or negligible fraction)
6. E-BFMI > 0.3 for all chains

If any diagnostic fails, do not trust the results until addressed.
