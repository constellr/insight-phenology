import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime
from matplotlib.colors import Normalize

def plot_gdd(gdd):

    fig, ax1 = plt.subplots()

    ax1.plot(gdd['date'], gdd['GDD'], color='blue', label='GDD')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('GDD', color='red')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(gdd['date'], gdd['interpol_NDVI'], color='green', label='NDVI')
    ax2.set_ylabel('NDVI', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))

    unique_stages = sorted(gdd['stage'].unique())
    colors = ['black', 'blue', 'green', 'yellow', 'orange']
    if len(unique_stages) < len(colors):
        colors = colors[:len(unique_stages)]

    for stage, color in zip(unique_stages, colors):
        stage_indices = gdd[gdd['stage'] == stage]['date']
        if len(stage_indices) > 0:
            ax1.axvspan(stage_indices.min(), stage_indices.max(), color=color, alpha=0.3, label=stage)

    ax1.set_title("GDD-derived crop growth stages")
    ax1.set_xlabel("date")
    ax1.set_ylabel("GDD")

    plt.show()

def plot_phenology(
        ndvi_ts, gdd_ts, plateaus, inflection_points, acceleration_points,
        peak_dates, peak_values, sos, pos, eos, gradients, max_val
    ):

    ndvi_interpol = ndvi_ts['interpol_NDVI'].values
    ndvi_filter = ndvi_ts['filter_NDVI'].values
    ndvi_dates = ndvi_ts['date'].values

    gdd_dates = gdd_ts['date'].values
    gdd_values = gdd_ts['GDD'].values

    fig, ax1 = plt.subplots()
    ax1.plot(ndvi_dates, ndvi_interpol, label='Raw NDVI', color='blue', linewidth=1.5)
    ax1.plot(ndvi_dates, ndvi_filter, label='Smooth NDVI', color='lightgreen', linewidth=1.5)

    ax2 = ax1.twinx()
    ax2.plot(gdd_dates, gdd_values, 'r-', label='GDD')
    ax2.set_ylabel('GDD', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    plt.figure(figsize=(12, 6))
    plt.plot(ndvi_dates, ndvi_interpol, label='Raw NDVI', color='blue', linewidth=1.5)
    plt.plot(ndvi_dates, ndvi_filter, label='Smooth NDVI', color='lightgreen', linewidth=1.5)

    for idx, plateau in enumerate(plateaus):
        start_date = ndvi_ts.loc[plateau[0], 'date']
        end_date = ndvi_ts.loc[plateau[-1] + 1, 'date'] if plateau[-1] + 1 < len(ndvi_ts) else ndvi_ts.loc[plateau[-1], 'date']
        plt.axvspan(start_date, end_date, color='yellow', alpha=0.3, label='Plateaus')

    plt.scatter(inflection_points['date'], inflection_points['filter'], color='black', label='Inflection Points',zorder=5)
    plt.scatter(acceleration_points['date'], acceleration_points['filter'], color='yellow', label='Acceleration Points',zorder=5)
    plt.plot(peak_dates, ndvi_ts['filter_NDVI'].iloc[peak_values], "x", color='red', label='Peaks')

    plt.axvline(sos, color="forestgreen", linestyle="-.", label=f"Start of Season (SOS)")
    plt.axvline(pos, color="forestgreen", linestyle="solid", label=f"Peak of Season (POS)")
    plt.axvline(eos, color="forestgreen", linestyle=":", label=f"End of Season (EOS)")

    unique_labels = []
    unique_handles = []
    handles, labels = plt.gca().get_legend_handles_labels()
    for handle, label in zip(handles, labels):
        if label not in unique_labels:
            unique_labels.append(label)
            unique_handles.append(handle)
            plt.legend(unique_handles, unique_labels)

    textstr = f'Growth rate:{np.round(gradients,2)}\nMaximum at POS:{np.round(max_val,2)}'
    plt.gca().text(0.5, 0.1, textstr, transform=plt.gca().transAxes,
                   fontsize=10, verticalalignment='bottom',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.title('NDVI phenology')
    plt.xlabel('Time')
    plt.ylabel('NDVI')
    plt.grid(True)
    plt.show()

def plot_all(
        merge_timeseries,
        ndvi_timeseries,
        gdd_timeseries,
        plateaus,
        inflection_points,
        acceleration_points,
        peaks, peak_dates, peak_values,
        sos_date, pos_date, eos_date,
        sos_value, eos_value,
        growth_rate, pos_value,
        startdate, enddate
):

    ndvi_interpol = ndvi_timeseries['interpol_NDVI'].values
    ndvi_filter = ndvi_timeseries['filter_NDVI'].values
    ndvi_dates = ndvi_timeseries['date'].values

    gdd_dates = gdd_timeseries['date'].values
    gdd_values = gdd_timeseries['GDD'].values

    fig, ax1 = plt.subplots()
    ax1.plot(ndvi_dates, ndvi_interpol, label='Raw NDVI', color='blue', linewidth=1.5)
    ax1.plot(ndvi_dates, ndvi_filter, label='Smooth NDVI', color='green', linewidth=1.5)
    ax1.plot(peak_dates, ndvi_timeseries['filter_NDVI'].iloc[peaks], "x", color='red', label='Peaks')

    plt.axvline(startdate, color="red", linestyle="-.", label=f"Sowing")
    plt.axvline(enddate, color="red", linestyle="solid", label=f"Harvest")

    ax2 = ax1.twinx()
    ax2.plot(gdd_dates, gdd_values, 'r-', label='GDD')

    """
    for idx, plateau in enumerate(plateaus):
        start_date = ndvi_timeseries.loc[plateau[0], 'date']
        end_date = ndvi_timeseries.loc[plateau[-1] + 1, 'date'] if plateau[-1] + 1 < len(ndvi_timeseries) else ndvi_timeseries.loc[
            plateau[-1], 'date']
        ax1.axvspan(start_date, end_date, color='gray', alpha=0.2, label='Plateaus')
    """

    ax1.scatter(inflection_points['date'], inflection_points['filter'], color='black', label='Inflection Points', zorder=5)
    ax1.scatter(acceleration_points['date'], acceleration_points['filter'], color='yellow', label='Acceleration Points', zorder=5)
    ax1.scatter(sos_date, sos_value, color='green', label='SOS', zorder=5)
    ax1.scatter(eos_date, eos_value, color='orange', label='EOS', zorder=5)

    merge_timeseries = merge_timeseries[merge_timeseries['stage'].notnull() & (merge_timeseries['stage'] != 'NaN')]
    #unique_stages = sorted(merge_timeseries['stage'].unique())
    unique_stages = merge_timeseries['stage'].unique()
    colors = ['blue', 'green', 'yellow', 'orange']
    if len(unique_stages) < len(colors):
        colors = colors[:len(unique_stages)]
    for stage, color in zip(unique_stages, colors):
        stage_indices = merge_timeseries[merge_timeseries['stage'] == stage]['date']
        #if len(stage_indices) > 0:
        ax1.axvspan(stage_indices.min(), stage_indices.max(), color=color, alpha=0.3, label=stage)
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    all_handles = handles1 + handles2
    all_labels = labels1 + labels2

    unique_labels = []
    unique_handles = []
    for handle, label in zip(all_handles, all_labels):
        if label not in unique_labels:
            unique_labels.append(label)
            unique_handles.append(handle)

    fig.legend(unique_handles, unique_labels, loc='upper right', bbox_to_anchor=(1, 1),
               bbox_transform=plt.gcf().transFigure)

    textstr = f'Growth rate:{np.round(growth_rate, 2)}\nMaximum at POS:{np.round(pos_value, 2)}'
    plt.gca().text(0.5, 0.1, textstr, transform=plt.gca().transAxes,
                   fontsize=10, verticalalignment='bottom',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    ax1.set_title("Crop growth stage derivation")
    ax1.set_xlabel("date")
    ax1.set_ylabel("NDVI", color='g')
    ax2.set_ylabel("GDD", color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    plt.grid(True)
    plt.show()

def plot_canopy_map(img, nearest_date, merged_image, cropland):

    cmap = plt.cm.gray
    norm = Normalize(vmin=np.min(img), vmax=np.max(img))

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    cax = ax[0].imshow(img, cmap=cmap, norm=norm)

    cbar = plt.colorbar(cax, ax=ax, orientation='horizontal', fraction=0.05, pad=0.1)
    cbar.set_label('NDVI', rotation=0, labelpad=10, color='black')
    cbar.ax.tick_params(labelcolor='black')
    cbar.set_label('NDVI')

    ax[0].set_title(f'NDVI Image at {nearest_date}')
    ax[0].axis('off')

    ax[1].imshow(merged_image, cmap='RdYlGn')
    ax[1].set_title(f'Canopy map at {nearest_date}')
    ax[1].axis('off')

    textstr = f'Net Area in %: {np.round(cropland, 2)}'
    plt.gca().text(
        0.5, 0.1, textstr, transform=plt.gca().transAxes,
        fontsize=10, verticalalignment='bottom',
        bbox=dict(
            boxstyle='round', facecolor='white'
        )
    )
    plt.show()

