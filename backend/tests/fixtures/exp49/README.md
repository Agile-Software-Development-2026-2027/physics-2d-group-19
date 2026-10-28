## Section 1 - File Origin

The documents within `backend` originate from the files shared by the Product Owner.

All downloaded files were verified via MD5 hash to ensure and exclude any data corruption or alteration during transfer.

---

## Section 2 - Files Present (`backend/tests/fixtures/exp49`)

* **`tAlgae49.txt`**  
  Represents the cell trajectories and spatio-temporal coordinates extracted from the legacy code via the tracking of video 49. Used as input for physical analysis services and as a benchmark in tracking module regression tests.

* **`illumination14.tiff`**  
  An image mapping the visual distribution of illumination field #14 used during laboratory testing. Serves as input for graphical functions and cell density calculations.

* **`talgae_settings.txt`**  
  Contains general laboratory parameters (line 49 specifically covers experiment 49): type, light intensity, and pixel/µm conversion factor. Provides the backend code with the configuration data required to initialize and execute physical processing on the dataset.

* **`tumb_exp49_tthres5.0.txt`**  
  The reference output for direction changes (*tumbling*) using a 5-second threshold. Utilized by automated CI tests to verify that the updated code produces results identical to the original implementation.


* **`tumb_dur_exp49_tthres5.0.txt`** 
  Contains data on the duration of individual tumbling events with a 5-second threshold. It serves as the reference laboratory output used in automated CI tests to validate the calculation of tumbling duration.

* **`Theta_exp49_FluoRadialised.txt`** 
  Maps the distribution of the theta angle, which describes the orientation of the algae. It is used in CI regression tests to verify that the new core calculates the exact same orientation profile.

* **`angle_exp49.txt`** 
  Contains the distribution of direction and movement angles for all tracked cells. Serves as a benchmark in automated tests to confirm the correctness of the angular distribution.   

* **`omega_exp49.txt`** 
  Collects the values of the Omega angular velocity, representing the rate of rotation/orientation change. Serves as official reference data in CI tests to ensure angular velocity matches the legacy code.