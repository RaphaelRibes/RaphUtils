from math import log

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from raphutils.functions import mean, std, median, first_quartile, third_quartile, iqr, outliers, remove_outliers, uncertainties_formating, dispersion, mustache_plot, units_combining
import pandas as pd


class GrowthMonitoring:
    def __init__(self, data_name, data_list, time):
        """
        :param data_name: the name of the data
        :param data_list: the list of the data
        :param time: the list of the time
        """
        self.name = data_name
        self.data = data_list
        self.time = np.array(time)
        self.package = {t: d for t, d in zip(self.time, self.data)}

        self.µ = [0]  # growth rate
        for i in range(len(data_list) - 1):
            d = (log(self.data[i + 1]) - log(self.data[i])) / (self.time[i + 1] - self.time[i])  # calculate the growth rate
            if d < 0:
                d = 0
            self.µ.append(d)
        self.µ = np.array(self.µ)  # convert the list to a numpy array

        self.td = []  # doubling time
        for i in range(len(self.µ)):
            if self.µ[i] != 0:
                d = log(2) / self.µ[i]  # calculate the doubling time
            else:
                d = 0
            self.td.append(d)
        self.td = np.array(self.td)  # convert the list to a numpy array

    def __str__(self):
        message = f"\n---------- {self.name} ----------"
        for i, time in enumerate(self.time):
            h = time // 60
            m = time % 60
            if h == 0:
                time = str(m)
            else:
                time = f'{h}h{m} min'
            message += f"\n| - {time} min: µ={self.µ[i] * 100:.3e}/min et Td={self.td[i]:.0f} min"
        message += '\n'
        message += '-' * len(f"---------- {self.name} ----------")
        return message

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.package.items())

    def plot(self, smoothing=False, smoothing_val=10, title=None):
        """
        Plots the growth rate and the doubling time of the data
        :param smoothing: the smoothing factor
        :param smoothing_val: the smoothing value
        :param title: the title of the graph
        :return:
        """
        fig, ax1 = plt.subplots()

        color = 'tab:red'
        ax1.set_xlabel('time (m)')
        ax1.set_ylabel('min⁻¹', color=color)
        if smoothing:
            spline = make_interp_spline(self.time, self.µ)  # create a spline
            time_ = np.linspace(self.time, self.µ,
                                len(self.time) * smoothing_val)  # create a list of time with the smoothing factor

            ax1.plot([t[-1] for t in time_],
                     [val[-1] for val in spline(time_)],
                     color=color, label='µ')
        else:
            ax1.plot(self.time, self.µ, color=color, label='µ')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        color = 'tab:blue'
        ax2.set_ylabel('min', color=color)  # we already handled the x-label with ax1
        ax2.tick_params(axis='y', labelcolor=color)
        if smoothing:
            spline = make_interp_spline(self.time, self.td)
            ax2.plot([t[-1] for t in time_], [val[-1] for val in spline(time_)], color=color, label='Td')
        else:
            ax2.plot(self.time, self.td, color=color, label='Td')

        if title:
            fig.legend(loc='lower right', fancybox=True, shadow=True)
            ax1.set_title(f'Évolution du taux de croissance et du temps de doublement'
                          f'\n de {self.name.lower()} en fonction du temps')
        else:
            fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1), ncol=2, fancybox=True, shadow=True)

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.show()


class Stat:
    def __init__(self, data_name, data_list, unit=None, discrete=False):
        self.name = data_name
        self.data = data_list
        self.unit = unit
        self.discrete = discrete

        self.mean = mean(data_list)
        self.std = std(data_list)
        self.median = median(data_list)
        self.first_quartile = first_quartile(data_list)
        self.third_quartile = third_quartile(data_list)
        self.iqr = iqr(data_list)
        self.outliers = outliers(data_list)
        self.data_no_outliers = remove_outliers(data_list)

    def __str__(self):
        message = (f"\n---------- {self.name} ----------"
                   f"\n| - Value: {self.mean:.3f} ± {self.std:.3f} {self.unit if self.unit else ''}"
                   f"\n| - Median: {self.median:.3f} {self.unit if self.unit else ''}"
                   f"\n| - First Quartile: {self.first_quartile:.3f} {self.unit if self.unit else ''}"
                   f"\n| - Third Quartile: {self.third_quartile:.3f} {self.unit if self.unit else ''}"
                   f"\n| - Interquartile Range: {self.iqr:.3f} {self.unit if self.unit else ''}"
                   f"\n| - Outliers: {', '.join([str(x) for x in self.outliers])}"
                   f"\n| - Dispersion: {dispersion(self.data)} {self.unit if self.unit else ''}"
                   f"\n| - Dispersion without outliers: {dispersion(self.data_no_outliers)} {self.unit if self.unit else ''}"
                   f"\n| - Standard error: {self.std / len(self.data) ** 0.5:.3f} {self.unit if self.unit else ''}")
        message += '\n|'
        if self.discrete: message += self.freq()
        message += '-' * len(f"---------- {self.name} ----------")
        return message

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, item):
        return item in self.data

    def __add__(self, other):
        if type(other) != Stat:
            raise TypeError(f"unsupported operand type(s) for +: 'Stat' and '{type(other)}'")
        elif self.unit != other.unit:
            raise ValueError(f"the units of the two data are not the same: '{self.unit}' and '{other.unit}'")
        self.data = [x + y for x, y in zip(self.data, other.data)]
        self.mean = mean(self.data)
        self.std = std(self.data)
        self.median = median(self.data)
        self.first_quartile = first_quartile(self.data)
        self.third_quartile = third_quartile(self.data)
        self.iqr = iqr(self.data)
        self.outliers = outliers(self.data)
        self.data_no_outliers = remove_outliers(self.data)

    def __sub__(self, other):
        if type(other) != Stat:
            raise TypeError(f"unsupported operand type(s) for -: 'Stat' and '{type(other)}'")
        elif self.unit != other.unit:
            raise ValueError(f"the units of the two data are not the same: '{self.unit}' and '{other.unit}'")
        self.data = [x - y for x, y in zip(self.data, other.data)]
        self.mean = mean(self.data)
        self.std = std(self.data)
        self.median = median(self.data)
        self.first_quartile = first_quartile(self.data)
        self.third_quartile = third_quartile(self.data)
        self.iqr = iqr(self.data)
        self.outliers = outliers(self.data)
        self.data_no_outliers = remove_outliers(self.data)

    def __mul__(self, other):
        if type(other) != Stat:
            raise TypeError(f"unsupported operand type(s) for *: 'Stat' and '{type(other)}'")
        self.data = [x * y for x, y in zip(self.data, other.data)]
        self.mean = mean(self.data)
        self.std = std(self.data)
        self.median = median(self.data)
        self.first_quartile = first_quartile(self.data)
        self.third_quartile = third_quartile(self.data)
        self.iqr = iqr(self.data)
        self.outliers = outliers(self.data)
        self.data_no_outliers = remove_outliers(self.data)
        self.unit = units_combining([self.unit, other.unit], '*')

    def __truediv__(self, other):
        if type(other) != Stat:
            raise TypeError(f"unsupported operand type(s) for /: 'Stat' and '{type(other)}'")
        self.data = [x / y for x, y in zip(self.data, other.data)]
        self.mean = mean(self.data)
        self.std = std(self.data)
        self.median = median(self.data)
        self.first_quartile = first_quartile(self.data)
        self.third_quartile = third_quartile(self.data)
        self.iqr = iqr(self.data)
        self.outliers = outliers(self.data)
        self.data_no_outliers = remove_outliers(self.data)
        self.unit = units_combining([self.unit, other.unit], '/')

    def freq(self, string=True):
        """
        Calculates the frequency of each modality
        """
        dt = {}
        for data in self.data:
            if data not in dt:
                dt[data] = 1
            else:
                dt[data] += 1

        if string:
            message = f"\n| - Number of modalities: {len(self.data)}"
            for data in dt:
                message += f"\n| - {data} : {dt[data]} -> {dt[data] / len(self.data) * 100:.2f}%"
            message += '\n'
        else:
            message = dt

        return message

    def plot(self):
        if self.discrete: self.freq_plot()
        else: self.classes_plot()
        mustache_plot([self.data], [self.name])

    def freq_plot(self):
        """
        Plots the frequency of each modality
        """
        data = self.freq(string=False)
        x = list(data.keys())
        if not self.discrete:
            print('\u001b[31m' + 'WARNING: the data is continuous, the graph may not be accurate.' + '\033[0m')

        x.sort()
        y = [data[key] / len(self.data) * 100 for key in x]
        fig, ax1 = plt.subplots()

        ax1.bar(x, y)
        ax1.set_xlabel(self.unit if self.unit else 'Valeur')
        ax1.set_ylabel('Fréquence (%)')
        ax1.set_title(f'Fréquence des valeurs de {self.name.lower()}')
        plt.show()

    def classes_plot(self):
        """
        Plots the frequency of each class
        """
        sturges = int(1 + log(len(self.data)))  # Sturges' formula
        dt = self.data.copy()  # copy of the data to avoid modifying it
        dt.sort()  # sort the data
        pas = (dt[-1] - dt[0])/sturges  # calculate the step
        y = [dt[0]+pas*i for i in range(sturges+1)]  # calculate the intervals

        x = []
        for i in range(len(y)-1):  # for each interval
            count = 0
            for data in dt:
                if y[i] <= data < y[i+1]:
                    count += 1
            x.append(count)
        x = [i/len(self.data)*100 for i in x]  # calculate the frequency
        # y_mid = [(y[i]+y[i+1])/2 for i in range(len(y)-1)]

        fig, ax1 = plt.subplots()

        # I stole that from stackoverflow and I don't know how it works
        # I only use it for putting pretty colors on the graph
        df = pd.Series(np.random.randint(10, 50, len(x)), index=np.arange(1, len(x) + 1))

        cmap = plt.cm.tab10
        colors = cmap(np.arange(len(df)) % cmap.N)
        # end of the stealing

        ax1.bar([f"[{y[i]:.2f}, {y[i+1]:.2f}[" for i in range(len(y)-1)],
                x, width=1, color=colors, edgecolor='black', linewidth=1.2)
        ax1.set_xlabel(self.unit if self.unit else 'Valeur')
        ax1.set_ylabel('Fréquence (%)')
        ax1.set_title(f'Fréquence des valeurs de {self.name.lower()}')
        fig.tight_layout()
        plt.show()


class Denombrement:
    def __init__(self, name, dilutions: dict):
        """
        Allow for the calculation of the concentration of a bacteria
        :param name: the name of the data
        :param dilutions: the dilutions of the data
        dilutions = {
            -4: None,
            -5: 354,
            -6: 35,
            -7: 3}
        """
        self.dilutions = dilutions
        self.name = name

    def __str__(self):
        message = f"\n------------- Dénombrement de {self.name} -------------"
        for dilution in self.dilutions:
            message += f"\n| - Dilution {10**dilution:.0e} : {self.dilutions[dilution] if self.dilutions[dilution] is not None else 'NC'} UFC"
        m, s = self.get_ufc_per_ml()
        message += f"\n|\n| - Concentration : {uncertainties_formating(m, s)} UFC/mL\n"
        message += "-"*len(f"------------- Dénombrement de {self.name} -------------")
        message = message.replace('1e', '10^')

        return message

    def get_ufc_per_ml(self):
        ufcs = []
        for dilution, ufc in self.dilutions.items():
            if ufc is None:
                continue
            if ufc < 30 or ufc > 600:
                continue
            else:
                ufcs.append(ufc * (10**-dilution))
        return mean(ufcs), std(ufcs)