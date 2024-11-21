import rasterio as rio, os
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from matplotlib.colors import Normalize

def get_file_with_nearest_date(dir_clip, target_date):
    date_file_map = {}
    directory = os.fsencode(dir_clip)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".tif") == True:
            date_str = filename.split('_')[2]
            file_date = datetime.strptime(date_str, '%Y%m%d')
            date_file_map[file_date] = filename

    nearest_date = None
    min_diff = None

    for date in date_file_map.keys():
        diff = abs(date - target_date)

        if min_diff is None or diff < min_diff:
            min_diff = diff
            nearest_date = date

    return date_file_map[nearest_date]

def get_parcel_image(dir_clip, pos_date, gid):

    pos_date = pos_date.strftime('%Y%m%d')
    pos_date = datetime.strptime(pos_date, '%Y%m%d')

    nearest_file = get_file_with_nearest_date(dir_clip, pos_date)
    nearest_name = nearest_file.split("_")[0]
    nearest_tile = nearest_file.split("_")[1]
    nearest_date = nearest_file.split("_")[2]

    parcel = f"{dir_clip}\\{nearest_name}_{nearest_tile}_{nearest_date}_NDVI_{gid}.tif"

    with rio.open(parcel) as src:
        img = src.read(1)

    return img, nearest_date

def clustering(img):
    x = img.reshape(-1, 1)
    num_clusters = 3

    kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(x)

    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_.flatten()

    sorted_indices = np.argsort(centroids)
    sorted_centroids = centroids[sorted_indices]

    sorted_labels_map = np.zeros_like(labels)
    for new_index, original_index in enumerate(sorted_indices):
        sorted_labels_map[labels == original_index] = new_index

    cluster_2_centroid = sorted_centroids[1]
    cluster_3_centroid = sorted_centroids[2]

    if abs(cluster_2_centroid - cluster_3_centroid) < 0.02:
        sorted_labels_map[sorted_labels_map == 2] = 1

    return sorted_labels_map

def postprocess(sorted_labels_map,img):
    x = img.reshape(-1, 1)
    merged_image = sorted_labels_map.reshape(img.shape)
    vals = np.unique(sorted_labels_map)
    img_mask = np.where(merged_image == vals[-1], 1, 0)

    netto_area = np.sum(img_mask)
    gross_area = np.where(x > 0, 1, 0)
    gross_area = np.sum(gross_area)
    cropland = (netto_area / gross_area) * 100

    return merged_image, cropland

def plot_map(img, nearest_date, merged_image, cropland):

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
