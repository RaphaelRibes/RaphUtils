from matplotlib import pyplot as plt
from math import exp, factorial
import numpy as np
import json


def box_plot(data, name, hide_outliers=True, vertical=True, title=False, save=False, path=None, unit=None):
    name = [n.lower() for n in name]
    fig, ax1 = plt.subplots()
    if title: ax1.set_title('Boxplot of {}'.format("\n".join(name)))

    ax1.boxplot(data, labels=name, showfliers=hide_outliers, vert=vertical)
    if unit is not None:
        ax1.set_ylabel(unit)
    fig.tight_layout()
    plt.show()

    if save:
        if path is None:
            path = f'Boxplot of {",".join(name)}'.replace("\n", ' ')
        else:
            path = f'{path}/Boxplot of {",".join(name)}'.replace("\n", ' ')
        fig.savefig(path, dpi=600)


def uncertainties_formating(mean, std):
    t_mean = f'{mean:.3e}'.split('e')
    t_std = f'{std:.3e}'.split('e')
    f_mean = int(t_mean[1])
    f_std = int(t_std[1])

    if f_mean > f_std:
        return f"({mean * 10 ** -f_mean:.3f} ± {std * 10 ** -f_mean:.3f})e{f_mean}"
    else:
        return f"({mean * 10 ** -f_std:.3f} ± {std * 10 ** -f_std:.3f})e{f_std}"


def units_combining(units, operation):
    """
    Combines two units; this is black magic I'm starting to forget how it works
    """
    if len(units) > 2: raise ValueError("Too many units")  # We can only combine two units at a time
    message = ''

    # If we are adding or subtracting, we don't need to combine the units
    if operation == '+':
        return units[0]
    elif operation == '-':
        return units[0]

    units = [u.split('/') for u in units]  # We split the units into numerator and denominator
    if operation in ['/', '*']:  # If we are multiplying or dividing
        if len(units[0]) == 1 and len(units[1]) == 1:  # If there is no division
            if operation == '/':
                message = units[0][0] + '/' + units[1][0]
            elif operation == '*':
                message = units[0][0] + '.' + units[1][0]

        elif len(units[0]) == 1 and len(units[1]) == 2:  # If there is a division in the denominator
            if operation == '/':
                units[1].reverse()
            message = units[0][0] + '.' + units[1][0] + '/' + units[1][1]

        elif len(units[0]) == 2 and len(units[1]) == 1:  # If there is a division in the numerator
            if operation == '/':
                message = units[0][0] + '/' + units[0][1] + units[1][0]
            if operation == '*':
                message = units[0][0] + '.' + units[1][0] + '/' + units[0][1]
        elif len(units[0]) == 2 and len(units[1]) == 2:  # If there is a division in the numerator and denominator
            if operation == '/':
                units[1].reverse()
            message = units[0][0] + '.' + units[1][0] + '/' + units[0][1] + '.' + units[1][1]

    units = message.split('/')
    units = [u.split('.') for u in units]
    _ = units[0].copy()  # We copy the list to avoid modifying it while iterating over it

    if operation == '/':  # If we are dividing, we need to cancel the units
        for u in _:
            if u in units[1]:
                units[1].remove(u)
                units[0].remove(u)
        message = '.'.join(units[0]) + '/' + '.'.join(units[1])
    else:
        if len(units[0]) == 1:
            message = '.'.join(units[0])

        else:  # If we are multiplying, we need to cancel the units
            if len(units) == 1:
                message = '.'.join(units[0])
            else:
                for i, u in enumerate(_):
                    if i == 0:
                        if u == units[1][i+1]:
                            units[1].remove(u)
                            units[0].remove(u)
                    else:
                        if u == units[1][i-1]:
                            units[1].remove(u)
                            units[0].remove(u)
                message = '.'.join(units[0]) + '/' + '.'.join(units[1])
    if '' in message.split('/'): message = message.split('/')[0]
    return message


def prettify(val, r=3):
    """
    If there is not more than r number, then the number is given back at it is
    Else, it returns a string of a float with r significant digits
    """
    if val == 0: return 0

    txt = f"{val:.{r}e}"
    index = abs(int(txt.split("e")[1]))
    if index <= r:
        msg = f"{round(val, r):.{r}f}"
        while msg.endswith('0'):
            msg = msg[:-1]
        if msg.endswith('.'):
            msg = msg[:-1]
        return msg
    else:
        return txt


def poisson(keys, mean):
    """
    Calculates the poisson distribution of the data
    """
    vals = {}
    for dt in keys:
        vals[dt] = exp(-mean) * (mean ** dt) / factorial(dt)
    return vals


def unbiased_nw_variance(data):
    """
    Calculates the unbiased variance of the data for a non-weighted mean
    """
    mean = np.mean(data)
    return sum([(x - mean) ** 2 for x in data]) / (len(data) - 1)


def unbiased_w_variance(data, weights):
    """
    Calculates the unbiased variance of the data for a weighted mean
    """
    mean = np.average(data, weights=weights)
    return sum([weights[i] * (x - mean) ** 2 for i, x in enumerate(data)]) / (sum(weights) - 1)


def biased_w_variance(data, weights):
    """
    Calculates the biased variance of the data for a weighted mean
    """
    mean = np.average(data, weights=weights)
    return sum([weights[i] * (x - mean) ** 2 for i, x in enumerate(data)]) / sum(weights)


def quantitative_confidence(var, n, u=1.96):
    interval = u * np.sqrt(var / n)
    return [float(prettify(var - interval)), float(prettify(var + interval))]


def probabilistic_confidence(prob, n, u=1.96):
    interval = u * np.sqrt(prob * (1 - prob) / n)
    return [float(prettify(prob - interval)), float(prettify(prob + interval))]


def bernoulli_law(x, n, p):
    return (factorial(n) / (factorial(n-x) * factorial(x))) * p**x * (1-p)**(n-x)


def positioning_chi2(obs, theo):
    # first we test if np_i >= 5
    fuck_up = []
    for i in range(len(obs)):
        if theo[i] < 5:
            fuck_up.append(prettify(theo[i]))
    if len(fuck_up) > 0:
        return f"np_i < 5 for {', '.join(fuck_up)}"
    return sum([(obs[i] - theo[i])**2/theo[i] for i in range(len(obs))])


def chi2_check(alpha, ddof, x2):
    with open('data/chi2.json', 'r') as f:
        table = json.load(f)

    _alpha_range = [0.9, 0.7, 0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.001]
    if alpha not in _alpha_range:
        raise ValueError(f"alpha must be in {', '.join([str(x) for x in _alpha_range])}")
    elif ddof not in [x for x in range(1, 31)]:
        raise ValueError(f"ddof must be an integer between 1 and 30")

    return table[str(ddof)][str(alpha)] >= x2


def r_squared(x, y, degree):
    # r-squared
    p = np.poly1d(np.polyfit(x, y, degree))
    # fit values, and mean
    yhat = p(x)                         # or [p(z) for z in x]
    ybar = np.sum(y)/len(y)          # or sum(y)/len(y)
    ssreg = np.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
    sstot = np.sum((y - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
    result = ssreg / sstot

    return result


def contingency_chi2(obs):
    """
    Calculates the chi2 of a set of observed and theoretical values
    obs is a list of list of observed values
    theo is a list of list of theoretical values
    return the chi2 value and ddl
    """
    x2 = 0
    row = [sum(obs[i]) for i in range(len(obs))]
    col = [sum([obs[i][j] for i in range(len(obs))]) for j in range(len(obs[0]))]
    total = sum(row)
    theo = [[row[i] * col[j] / total for j in range(len(col))] for i in range(len(row))]
    for i in range(len(obs)):
        for j in range(len(obs[0])):
            x2 += (obs[i][j] - theo[i][j])**2/theo[i][j]
    return x2, (len(obs)-1)*(len(obs[0])-1), theo
