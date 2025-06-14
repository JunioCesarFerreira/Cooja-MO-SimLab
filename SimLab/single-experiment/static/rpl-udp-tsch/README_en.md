# Unit Experiments

This directory contains materials for running isolated simulations, with the goal of evaluating the proposed metrics and verifying the functionality of the Cooja simulator.

## Usage Workflow

1. **Topology Configuration**

   Open the notebook [`fix-motes-pos.ipynb`](fix-motes-pos.ipynb). This notebook allows you to visualize the experiment's topology and generate the file `data/inputExample.json`. To do this, modify the line `exp_index = n`, where `n` is the desired experiment index, and execute the last code cell.

2. **Initializing the Cooja Environment**

   Launch a Cooja container using the [setup guide available here](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja). For example, you can use the [docker-compose configuration provided in the PoC](../poc/simlab/docker-compose.yaml).

3. **Generating the Simulation File**

   In the `single-experiment` directory, run the following command:
   ```bash
   python main.py
````

This will generate the file `output/simulation.xml`, based on the data located in the `data` directory, including the XML template and the JSON file created in the previous step.

4. **Transferring the Simulation File to the Container**

   In the `~/Cooja-MO-SimLab/SimLab/single-experiment/output` directory, use the command below to transfer the files to the container:

   ```bash
   scp -P 2231 * root@127.0.0.1:/opt/contiki-ng/tools/cooja
   ```

5. **Accessing the Container via SSH**

   Connect to the container using:

   ```bash
   ssh -p 2231 root@127.0.0.1
   ```

   For more details, refer again to the [container setup guide](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja).

6. **Preparing the Simulation File in the Container**

   Inside the container, navigate to `/opt/contiki-ng/tools/cooja` and rename the file:

   ```bash
   mv simulation.xml simulation.csc
   ```

7. **Running the Simulation**

   Run Cooja in headless mode using:

   ```bash
   java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
   ```

8. **Wait for the Simulation to Finish**

9. **Retrieving the Simulation Log**

   After execution, retrieve the simulation log file with:

   ```bash
   scp -P 2231 root@127.0.0.1:/opt/contiki-ng/tools/cooja/COOJA.testlog cooja.log
   ```

10. **Organizing the Experiment Results**

    * Create a directory named `expN`, where `N` is the experiment number.
    * Copy the following files into this directory:

      * `data/inputExample.json`
      * `cooja.log`
      * The notebook `expN-1.ipynb`, renaming it to `expN.ipynb`
    * Update the descriptive text in the notebook and run all cells.
