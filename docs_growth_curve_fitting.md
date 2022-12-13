Dashing Growth Curves offers different methods to extract growth parameters from microbial growth curves.

# Variables in all models
$N$: population size measure (can be optical density measurements, colony forming unit counts or similar)

$y = log(N)$

$\mu_{max}$: maximum growth rate

$A$: maximum population density

$\lambda$: lag time as defined by the x-axis intersect of the tangent at the inflexion point of the growth model (see figure below).

# Growth Models
## 1. Logistic
This option fits all growth curves to the modified Logistic growth model[^1]:

$$y = \frac{A}{1 + \exp[\frac{4\mu_{max}}{A} (\lambda - t) + 2]}$$

## 2. Logistic - tight
This option fits the same model as described above, but uses a different definition of the lag time. Here, the lag time is the smallest zero of third derivative of the Logistic function. Generally, the 'tight' lag time is greater than the standard lag time (see figure below)[^2].
## 5. Gompertz
This option fits all growth curves to the modified Gompertz growth model[^1]:

$$y = \exp(-\exp( \frac{\mu_{max} \cdot e}{A} (\lambda - t) + 1))$$

## 6. Gompertz - tight
This option fits the same model as described above, but used the 'tight' definition of the lag time[^2].

## Lag time definitions

![](./figures/lag_time_definition.jpg)




# References
[^1]: Zwietering et al., 1990 (https://doi.org/10.1128/aem.56.6.1875-1881.1990)
[^2]: Zwietering et al., 1992 (https://doi.org/10.1111/j.1365-2672.1992.tb01815.x)