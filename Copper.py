import random
import multiprocessing
import os
import sys
import matplotlib.pyplot as plt
from collections import Counter
from litemapy import Schematic, BlockState

blocks_to_track = ["minecraft:copper_block", "minecraft:exposed_copper", "minecraft:weathered_copper", "minecraft:oxidized_copper"]
plot_interval = 100
random_tick_chance_per_block=3/(16**3)
warp_ticks=72000*8


def load_schematic(file_path):
    schem = Schematic.load(file_path)
    if len(schem.regions.values())!=1: raise Exception("Only litematics with 1 region supported")
    return schem


def analyse_schematic(schem, name):
    region = next(iter(schem.regions.values()))

    data_history = {block_id: [] for block_id in blocks_to_track}
    iterations = []

    # collect initial copper positions
    copper_positions = []
    for x in range(region.width):
        for y in range(region.height):
            for z in range(region.length):
                block = region[(x, y, z)]
                if block.id == "minecraft:copper_block":
                    copper_positions.append((x, y, z))

    for i in range(warp_ticks):
        for position in copper_positions:
            if random.random() < random_tick_chance_per_block:
                randomtick(position, region)
        if i % plot_interval==0:
            collect_data(copper_positions, region, i, data_history, iterations)
    plot_data(data_history, iterations, name)


def plot_data(data_history, iterations, name):
    fig, ax = plt.subplots()
    ax.set_xlabel("Hours")
    ax.set_ylabel("Percentage of Blocks")
    plt.gcf().canvas.manager.set_window_title(name)

    for block_id, values in data_history.items():
        if len(iterations) > 1:
            ax.plot(iterations, values, label=block_id)

    ax.legend()
    plt.show()


def collect_data(copper_positions, region, i, data_history, iterations):
    counts = Counter(region[pos].id for pos in copper_positions)
    iterations.append(i/72000)

    for block_id in blocks_to_track:
        data_history[block_id].append(counts.get(block_id, 0)/ len(copper_positions)*100)


def randomtick(position, region):
    i = id_to_level(region[position].id)
    degradation_chance_multiplier=0.75 if i==0 else 1.0
    max_distance=4
    c = 0.05688889
    if random.random() < c:
        j=0
        k=0

        x0, y0, z0 = position
        for x in range(x0 - max_distance, x0 + max_distance + 1):
            for y in range(y0 - max_distance, y0 + max_distance + 1):
                for z in range(z0 - max_distance, z0 + max_distance + 1):
                    manhattan_distance = abs(x - x0) + abs(y - y0) + abs(z - z0)
                    if manhattan_distance > max_distance or x<0 or y<0 or z<0 or x>region.width-1 or y>region.height-1 or z>region.length-1 :
                        continue
                    m = id_to_level(region[(x, y, z)].id)
                    if (x, y, z) != position and m != -1:
                        if m<i:
                            return
                        if m>1:
                            k+=1
                        else:
                            j+=1
        f = (k + 1) / (k + j + 1)
        g = f * f * degradation_chance_multiplier

        if random.random()<g:
            new_block = BlockState(level_to_id(i+1 if i<3 else 3))
            region[position]=new_block


def id_to_level(id):
    match id:
        case "minecraft:copper_block":
            return 0
        case "minecraft:exposed_copper":
            return 1
        case "minecraft:weathered_copper":
            return 2
        case "minecraft:oxidized_copper":
            return 3
        case _:
            return -1


def level_to_id(level):
    return blocks_to_track[level]


if __name__ == '__main__':
    #Enter schematic directory containing all flies that shell be tested
    if len(sys.argv) < 2:
        print("Error: Please Enter schematic directory.")
        sys.exit(1)

    directory_path = sys.argv[1]

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        sys.exit(1)

    processes = []

    for filename in os.listdir(directory_path):
        if filename.endswith(".litematic"):
            file_path = os.path.join(directory_path, filename)
            name = os.path.splitext(filename)[0]  # remove ".litematic" ending
            p = multiprocessing.Process(target=analyse_schematic, args=(load_schematic(file_path), name))
            p.start()
            processes.append(p)

    # Wait for finish
    for p in processes:
        p.join()
