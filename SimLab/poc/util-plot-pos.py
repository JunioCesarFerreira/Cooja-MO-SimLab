import os
import matplotlib.pyplot as plt

def plot_file_positions(filename="positions.dat", fileoutput="positions.png"):
    fixed_positions = []
    mobile_positions = {}
    
    with open(filename, "r") as file:
        for line in file:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.split()
            mote_id, _, x, y = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            
            if mote_id not in mobile_positions and len(fixed_positions) > mote_id:
                fixed_positions.append((x, y))
            else:
                if mote_id not in mobile_positions:
                    mobile_positions[mote_id] = []
                mobile_positions[mote_id].append((x, y))
                
    plt.figure(figsize=(8, 8))
    
    # Plot fixed motes
    if fixed_positions:
        x_fixed, y_fixed = zip(*fixed_positions)
        plt.scatter(x_fixed, y_fixed, color='red', marker='o', label='Fixed Nodes')
    
    # Plot mobile motes
    for mote_id, positions in mobile_positions.items():
        x_mobile, y_mobile = zip(*positions)
        plt.plot(x_mobile, y_mobile, marker='o', linestyle='-', label=f'Mobile Node {mote_id}')
    
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.title("Node Positions")
    plt.grid()    
    plt.axis("equal")
    plt.savefig(fileoutput)
    

directory = "tmp"
if not os.path.isdir(directory):
    print(f"Directory not found: {directory}")
else:
    dat_files = [f for f in os.listdir(directory) if f.endswith('.dat') and os.path.isfile(os.path.join(directory, f))]

    print(f".dat files in '{directory}':")
    for file in dat_files:
        path = os.path.join(directory, file)
        plot_file_positions(path, str.replace(path, ".dat", ".png"))
