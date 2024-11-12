import matplotlib.pyplot as plt
import numpy as np

def plot_phenology(
        ndvi_ts, gdd_ts, plateaus, inflection_points,
        acceleration_1, acceleration_2, acceleration_3, acceleration_4,
        peak_dates, peaks, sos, pos, eos, gradients, max_val
    ):

    ndvi_interpol = ndvi_ts['interpol'].values
    ndvi_gaussian = ndvi_ts['gaussian'].values
    ndvi_dates = ndvi_ts['date'].values

    gdd_dates = gdd_ts['date'].values
    gdd_values = gdd_ts['GDD'].values

    fig, ax1 = plt.subplots()
    ax1.plot(ndvi_dates, ndvi_interpol, label='Raw NDVI', color='blue', linewidth=1.5)
    ax1.plot(ndvi_dates, ndvi_gaussian, label='Smooth NDVI', color='lightgreen', linewidth=1.5)

    ax2 = ax1.twinx()
    ax2.plot(gdd_dates, gdd_values, 'r-', label='GDD')
    ax2.set_ylabel('GDD', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(ndvi_dates, ndvi_interpol, label='Raw NDVI', color='blue', linewidth=1.5)
    plt.plot(ndvi_dates, ndvi_gaussian, label='Smooth NDVI', color='lightgreen', linewidth=1.5)

    for idx, plateau in enumerate(plateaus):
        start_date = ndvi_ts.loc[plateau[0], 'date']
        end_date = ndvi_ts.loc[plateau[-1] + 1, 'date'] if plateau[-1] + 1 < len(ndvi_ts) else ndvi_ts.loc[plateau[-1], 'date']
        plt.axvspan(start_date, end_date, color='yellow', alpha=0.3, label='Plateaus')

    plt.scatter(inflection_points['date'], inflection_points['gaussian'], color='black', label='Stage Change',zorder=5)
    plt.scatter(acceleration_1['date'], acceleration_1['gaussian'], color='green', label='Canopy Closing',zorder=5)
    plt.scatter(acceleration_3['date'], acceleration_3['gaussian'], color='red', label='Start vegetative period', zorder=5)

    plt.plot(peak_dates, ndvi_ts['gaussian'].iloc[peaks], "x", color='red', label='Peaks')
    plt.scatter(acceleration_2['date'], acceleration_2['gaussian'], color='orange', label='Start of Maturity',zorder=5)
    plt.scatter(acceleration_4['date'], acceleration_4['gaussian'], color='magenta', label='Start of Senescence', zorder=5)

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
