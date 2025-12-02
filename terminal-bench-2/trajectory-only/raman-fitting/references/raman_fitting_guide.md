# Raman Spectroscopy Peak Fitting Reference Guide

## Data Format Considerations

### Common File Formats
- **Tab-separated values (TSV)**: Columns separated by `\t`
- **Comma-separated values (CSV)**: Columns separated by `,`
- **Locale-specific formats**: European locales may use `,` as decimal separator

### Parsing Strategies
```python
# Handle European decimal format (comma as decimal separator)
def parse_european_number(s):
    """Convert European number format to float."""
    return float(s.replace(',', '.'))

# Robust data loading
def load_raman_data(filepath, delimiter='\t'):
    """Load Raman data with format detection."""
    with open(filepath, 'r') as f:
        first_line = f.readline().strip()

    # Detect if comma is used as decimal separator
    if ',' in first_line and '.' not in first_line:
        # European format
        data = np.genfromtxt(filepath, delimiter=delimiter,
                            converters={0: parse_european_number,
                                       1: parse_european_number})
    else:
        data = np.loadtxt(filepath, delimiter=delimiter)

    return data[:, 0], data[:, 1]  # wavenumber, intensity
```

### Data Quality Checks
```python
def check_data_quality(wavenumber, intensity):
    """Perform basic data quality checks."""
    print(f"Wavenumber range: {wavenumber.min():.1f} - {wavenumber.max():.1f} cm⁻¹")
    print(f"Number of data points: {len(wavenumber)}")
    print(f"Intensity range: {intensity.min():.1f} - {intensity.max():.1f}")

    # Check for expected graphene peaks
    expected_peaks = {'D': 1350, 'G': 1580, '2D': 2700}
    for name, pos in expected_peaks.items():
        if wavenumber.min() <= pos <= wavenumber.max():
            print(f"✓ {name} peak region ({pos} cm⁻¹) is within data range")
        else:
            print(f"✗ {name} peak region ({pos} cm⁻¹) is OUTSIDE data range")
```

## Peak Functions

### Lorentzian
```python
def lorentzian(x, amplitude, center, gamma):
    """
    Lorentzian peak function.

    Parameters:
        x: wavenumber array
        amplitude: peak intensity
        center: peak position (cm⁻¹)
        gamma: half-width at half-maximum (cm⁻¹)

    Returns:
        Intensity values
    """
    return amplitude * gamma**2 / ((x - center)**2 + gamma**2)
```

### Gaussian
```python
def gaussian(x, amplitude, center, sigma):
    """
    Gaussian peak function.

    Parameters:
        x: wavenumber array
        amplitude: peak intensity
        center: peak position (cm⁻¹)
        sigma: standard deviation (FWHM = 2.355 * sigma)

    Returns:
        Intensity values
    """
    return amplitude * np.exp(-(x - center)**2 / (2 * sigma**2))
```

### Voigt (using scipy)
```python
from scipy.special import voigt_profile

def voigt(x, amplitude, center, sigma, gamma):
    """
    Voigt peak function (convolution of Gaussian and Lorentzian).

    Parameters:
        x: wavenumber array
        amplitude: scaling factor
        center: peak position (cm⁻¹)
        sigma: Gaussian width
        gamma: Lorentzian width

    Returns:
        Intensity values
    """
    return amplitude * voigt_profile(x - center, sigma, gamma)
```

### Pseudo-Voigt
```python
def pseudo_voigt(x, amplitude, center, fwhm, eta):
    """
    Pseudo-Voigt: linear combination of Gaussian and Lorentzian.

    Parameters:
        eta: mixing parameter (0 = pure Gaussian, 1 = pure Lorentzian)
    """
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    gamma = fwhm / 2

    gauss = np.exp(-(x - center)**2 / (2 * sigma**2))
    lorentz = gamma**2 / ((x - center)**2 + gamma**2)

    return amplitude * (eta * lorentz + (1 - eta) * gauss)
```

## Background Subtraction Methods

### Linear Baseline
```python
def linear_baseline(wavenumber, intensity, regions):
    """
    Fit linear baseline using specified regions.

    Parameters:
        regions: list of (start, end) tuples for baseline regions
    """
    baseline_x, baseline_y = [], []
    for start, end in regions:
        mask = (wavenumber >= start) & (wavenumber <= end)
        baseline_x.extend(wavenumber[mask])
        baseline_y.extend(intensity[mask])

    coeffs = np.polyfit(baseline_x, baseline_y, 1)
    return np.polyval(coeffs, wavenumber)
```

### Asymmetric Least Squares (ALS)
```python
from scipy import sparse
from scipy.sparse.linalg import spsolve

def baseline_als(y, lam=1e6, p=0.01, niter=10):
    """
    Asymmetric Least Squares baseline correction.

    Parameters:
        y: intensity array
        lam: smoothness parameter (larger = smoother)
        p: asymmetry parameter (smaller = more asymmetric)
        niter: number of iterations
    """
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L-2))
    w = np.ones(L)

    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)

    return z
```

## Fitting Workflow Template

```python
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def complete_peak_fitting(filepath, peak_name, region, expected_position):
    """
    Complete workflow for fitting a single Raman peak.
    """
    # Step 1: Load and explore data
    wavenumber, intensity = load_raman_data(filepath)
    check_data_quality(wavenumber, intensity)

    # Step 2: Extract fitting region
    mask = (wavenumber >= region[0]) & (wavenumber <= region[1])
    x_fit = wavenumber[mask]
    y_fit = intensity[mask]

    if len(x_fit) < 10:
        raise ValueError(f"Insufficient data points in region {region}")

    # Step 3: Background subtraction
    baseline = np.polyval(np.polyfit([x_fit[0], x_fit[-1]],
                                      [y_fit[0], y_fit[-1]], 1), x_fit)
    y_corrected = y_fit - baseline

    # Step 4: Initial guess
    idx_max = np.argmax(y_corrected)
    initial_guess = [y_corrected[idx_max], x_fit[idx_max], 20]  # amp, center, gamma

    # Step 5: Set bounds
    bounds = ([0, region[0], 5],
              [np.inf, region[1], 200])

    # Step 6: Fit with multiple functions
    results = {}
    for func_name, func in [('lorentzian', lorentzian),
                            ('gaussian', gaussian)]:
        try:
            popt, pcov = curve_fit(func, x_fit, y_corrected,
                                   p0=initial_guess, bounds=bounds)

            # Calculate R²
            y_pred = func(x_fit, *popt)
            ss_res = np.sum((y_corrected - y_pred)**2)
            ss_tot = np.sum((y_corrected - np.mean(y_corrected))**2)
            r_squared = 1 - ss_res / ss_tot

            results[func_name] = {
                'params': popt,
                'errors': np.sqrt(np.diag(pcov)),
                'r_squared': r_squared
            }
        except Exception as e:
            results[func_name] = {'error': str(e)}

    # Step 7: Select best fit
    best_fit = max(results.items(),
                   key=lambda x: x[1].get('r_squared', 0))

    # Step 8: Validate
    if best_fit[1].get('r_squared', 0) < 0.5:
        print(f"WARNING: Best R² = {best_fit[1]['r_squared']:.3f} < 0.5")

    fitted_position = best_fit[1]['params'][1]
    if abs(fitted_position - expected_position) > 50:
        print(f"WARNING: Fitted position {fitted_position:.1f} differs from "
              f"expected {expected_position} by > 50 cm⁻¹")

    return results, best_fit
```

## Graphene-Specific Information

### Expected Peak Parameters

| Peak | Position (cm⁻¹) | Typical FWHM (cm⁻¹) | Origin |
|------|-----------------|---------------------|--------|
| D | 1350 | 30-50 | Disorder/defects |
| G | 1580 | 15-25 | E₂g phonon mode |
| D' | 1620 | 10-20 | Disorder |
| 2D | 2700 | 30-60 | Two-phonon process |
| D+D' | 2940 | 40-60 | Combination mode |

### Quality Indicators

- **I(2D)/I(G) ratio**: > 2 indicates single-layer graphene
- **I(D)/I(G) ratio**: Indicates defect density (lower is better)
- **2D peak FWHM**: < 30 cm⁻¹ for single-layer graphene

### Position Shifts

Peak positions can shift due to:
- **Strain**: Both D and 2D peaks shift
- **Doping**: G peak shifts and broadens
- **Number of layers**: 2D peak shape changes
- **Laser wavelength**: D peak position is dispersive (~50 cm⁻¹/eV)
