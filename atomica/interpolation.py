#%% Imports

from atomica.system import AtomicaException, logger

from copy import deepcopy as dcp
import numpy as np


#%% General interpolation wrapper

def interpolateFunc(x, y, xnew, method = 'pchip', extrapolate_nan = False):
    '''
    Function that interpolates and extrapolates (x,y) coordinates along the domain subset of xnew, according to a chosen method.
    Works with numpy arrays to standardise output types. Input must be numpy array compatible.    
    IMPORTANT: If you do not use this wrapper to apply interpolations, data will not be error-checked.
    '''
    
    try:
        # Note np.ndarray.astype() returns a copy
        x = x.astype(float)
        y = y.astype(float)
        xnew = xnew.astype(float)
    except:
        raise AtomicaException('ERROR: Interpolation received values that cannot be converted into numpy float arrays.')
    
    if not len(x) > 1: raise AtomicaException('ERROR: Interpolation failure due to the existence of less than two x values.')
    if not len(x) == len(y): raise AtomicaException('ERROR: Interpolation failure due to unequal number of x and y values.')
    if len(set(x)) != len(x): raise AtomicaException('ERROR: Interpolation failure due to repeated x values.')
    
    # Sorts all input vectors.
    idx = np.argsort(x) # Index order to sort arrays
    x = x[idx]
    y = y[idx]
    xnew = np.sort(xnew) # np.sort() returns a copy

    if method == 'pchip':
        m = pchipSlopes(x, y)                           # Compute slopes used by piecewise cubic Hermite interpolator.
        ynew = pchipEval(x, y, m, xnew, deriv = False)  # Use these slopes (along with the Hermite basis function) to interpolate.
    
#    elif method=='smoothinterp':
#        ...
    
    else:
        raise AtomicaException('ERROR: Interpolation method "%s" not understood.' % method)
        
    # Replace extrapolated values with np.nan if this tag is marked True.
    if extrapolate_nan:
        ynew[xnew<x[0]] = np.nan
        ynew[xnew>x[-1]] = np.nan
    
    return ynew
    
#%% Implementation of the monotonic Piecewise Cubic Hermite Interpolating Polynomial (PCHIP)
    
def pchipSlopes(x, y):
    '''
    Determine slopes to be used for the PCHIP method.
    Slopes are constrained via the Fritsch-Carlson method.
    
    More details: https://en.wikipedia.org/wiki/Monotone_cubic_interpolation
    Script written by Chris Michalski 2009aug18 used as a basis.
    
    Version: 2016sep22
    '''

    m = np.zeros(len(x))
    secants = np.diff(y)/np.diff(x)
    
    for c in range(len(x)):
        if c == 0: deriv = secants[c]
        elif c == len(x)-1: deriv = secants[c-1]
        elif secants[c]*secants[c-1] <= 0: deriv = 0
        else: deriv = (secants[c]+secants[c-1])/2
        
        if c < len(x)-1 and abs(deriv) > 3*abs(secants[c]): deriv = 3*secants[c]
        if c > 0 and abs(deriv) > 3*abs(secants[c-1]): deriv = 3*secants[c-1]

        m[c] = deriv

    return np.array(m)


def pchipEval(x, y, m, xvec, deriv = False):
    '''
    Evaluate the piecewise cubic Hermite interpolant with monotonicity preserved. Interpolate for xvec.
    Array x must be monotonically increasing with no repeats, but y can have repeated values.
    Due to the cubic nature of extrapolation, it is recommended that xvec[0]=x[0] and xvec[-1]=x[-1].
    
    More details: https://en.wikipedia.org/wiki/Monotone_cubic_interpolation
    Script written by Chris Michalski 2009aug18 used as a basis.
    
    Version: 2016sep22
    '''
    
    yvec = np.zeros(len(xvec))
    
    oid = 0     # Old id. Tracking index for x and y.
    nid = 0     # New id. Tracking index for xnew and ynew.
    for xc in xvec:
        while xc < x[-1] and xc >= x[oid+1]:
            oid += 1
        if xc >= x[-1]: oid = -2
        
        # Create the Hermite coefficients.
        h = x[oid+1] - x[oid]
        t = (xc - x[oid]) / h
        
        # Hermite basis functions.
        if not deriv:
            h00 = (2 * t**3) - (3 * t**2) + 1
            h10 =      t**3  - (2 * t**2) + t
            h01 = (-2* t**3) + (3 * t**2)
            h11 =      t**3  -      t**2
        else:
            h00 = ((6 * t**2) - (6 * t**1))/h
            h10 = ((3 * t**2) - (4 * t**1) + 1)/h
            h01 = ((-6* t**2) + (6 * t**1))/h
            h11 = ((3 * t**2) - (2 * t**1))/h
        
        # Compute the interpolated value of y.
        ynew = h00*y[oid] + h10*h*m[oid] + h01*y[oid+1] + h11*h*m[oid+1]
        yvec[nid] = ynew
        nid += 1
    
    return yvec