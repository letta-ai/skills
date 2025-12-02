# Hierarchical Bayesian Models in Stan

## Model Structure Overview

Hierarchical (multilevel) models have three components:

1. **Likelihood**: p(y | θ) - How data relates to group-level parameters
2. **Prior**: p(θ | φ) - How group parameters relate to hyperparameters
3. **Hyperprior**: p(φ) - Distribution over population-level parameters

## Common Hierarchical Model Patterns

### Beta-Binomial Hierarchical Model

Classic example for grouped count data (e.g., rat tumor experiments):

```stan
data {
  int<lower=0> N;              // Number of groups
  int<lower=0> y[N];           // Successes per group
  int<lower=0> n[N];           // Trials per group
}

parameters {
  real<lower=0> alpha;         // Beta shape parameter 1
  real<lower=0> beta;          // Beta shape parameter 2
  real<lower=0, upper=1> theta[N];  // Group success probabilities
}

model {
  // Hyperprior: p(α,β) ∝ (α+β)^(-5/2)
  target += -2.5 * log(alpha + beta);

  // Prior: theta_i ~ Beta(α, β)
  theta ~ beta(alpha, beta);

  // Likelihood: y_i ~ Binomial(n_i, θ_i)
  y ~ binomial(n, theta);
}

generated quantities {
  // Posterior predictive for new group
  real<lower=0, upper=1> theta_new;
  theta_new = beta_rng(alpha, beta);
}
```

### Normal Hierarchical Model

For continuous outcomes with group structure:

```stan
data {
  int<lower=0> N;              // Total observations
  int<lower=0> J;              // Number of groups
  int<lower=1, upper=J> group[N];  // Group membership
  real y[N];                   // Outcomes
}

parameters {
  real mu;                     // Population mean
  real<lower=0> tau;           // Between-group SD
  real<lower=0> sigma;         // Within-group SD
  real theta[J];               // Group means
}

model {
  // Hyperpriors
  mu ~ normal(0, 10);
  tau ~ cauchy(0, 5);
  sigma ~ cauchy(0, 5);

  // Group-level priors
  theta ~ normal(mu, tau);

  // Likelihood
  for (i in 1:N)
    y[i] ~ normal(theta[group[i]], sigma);
}
```

## Prior Specification Guidance

### Weakly Informative Priors

For scale parameters (standard deviations):
```stan
sigma ~ cauchy(0, 5);      // Heavy-tailed, allows large values
sigma ~ normal(0, 10);     // Truncated at 0 due to constraint
sigma ~ exponential(1);    // If expecting small values
```

For location parameters:
```stan
mu ~ normal(0, 10);        // Centered, moderate spread
mu ~ student_t(3, 0, 10);  // Robust to outliers
```

### Improper/Custom Priors

Implement via `target +=` increment:

```stan
// p(x) ∝ 1 (flat prior) - no statement needed

// p(x) ∝ 1/x (Jeffreys for scale)
target += -log(x);

// p(α,β) ∝ (α+β)^(-5/2) (common for Beta hyperparameters)
target += -2.5 * log(alpha + beta);

// p(σ) ∝ 1/σ (Jeffreys for variance)
target += -log(sigma);
```

## Reparameterization Techniques

### Non-Centered Parameterization

When hierarchical models show divergent transitions:

**Centered (may have issues)**:
```stan
parameters {
  real mu;
  real<lower=0> tau;
  real theta[J];
}
model {
  theta ~ normal(mu, tau);
}
```

**Non-centered (often better)**:
```stan
parameters {
  real mu;
  real<lower=0> tau;
  real theta_raw[J];  // Standard normal
}
transformed parameters {
  real theta[J];
  for (j in 1:J)
    theta[j] = mu + tau * theta_raw[j];
}
model {
  theta_raw ~ normal(0, 1);
}
```

### When to Use Each

| Data Scenario | Preferred Parameterization |
|---------------|---------------------------|
| Many observations per group | Centered |
| Few observations per group | Non-centered |
| Moderate data | Try both, compare |

## Data Preparation Best Practices

### R Data List Format

```r
stan_data <- list(
  N = nrow(data),
  J = length(unique(data$group)),
  y = data$outcome,
  n = data$trials,
  group = as.integer(factor(data$group))
)
```

### Validation Before Sampling

```r
# Check data dimensions match
stopifnot(length(stan_data$y) == stan_data$N)
stopifnot(all(stan_data$y >= 0))
stopifnot(all(stan_data$y <= stan_data$n))
```

## Posterior Summarization

### Extracting Results

```r
# Summary statistics
print(fit, pars = c("alpha", "beta", "theta"))

# Extract samples as array
samples <- extract(fit, permuted = TRUE)
alpha_samples <- samples$alpha
beta_samples <- samples$beta

# Compute derived quantities
population_mean <- alpha_samples / (alpha_samples + beta_samples)
mean(population_mean)
quantile(population_mean, c(0.025, 0.975))
```

### Posterior Predictive Checks

```r
# If generated quantities included theta_new
theta_new_samples <- samples$theta_new

# Plot posterior predictive
hist(theta_new_samples, main = "Posterior Predictive for New Group")
```
