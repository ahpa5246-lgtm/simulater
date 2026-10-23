# Executable MPU-6050 IMU model (experimental)

This vertical slice adds a real Arduino Wire-compatible I²C *behavioral register model*, not a fabricated animation. Open `/lab.html`, select `MPU-6050 motion sensor (I²C)`, load the experiment and compile/run. The sketch wakes the sensor, reads 14 consecutive bytes starting at 0x3B and turns on LED D13 if AX is positive. With default vector values, UART should show `AX:8192 AZ:16384 GY:11790`. Adjust acceleration X/Y/Z (g), gyro X/Y/Z (degrees/s) and temperature; rerun to inspect real AVR UART and I²C logs.

Supported: addresses 0x68/0x69 (both WHO_AM_I 0x68), power-on sleep and reset via PWR_MGMT_1, PWR_MGMT_2 axis standby, 4 accel full-scale modes, 4 gyro full-scale modes, signed big-endian accel/temperature/gyro registers, and I²C register-pointer reads. Inputs are constant during a run; output clips to signed 16-bit range. Register mapping is based on TDK InvenSense MPU-6000/6050 Register Map RM-MPU-6000A-00 Rev 4.2 (https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf), without copying proprietary code or assets.

Not supported: actual 3D rigid-body dynamics, FIFO, DMP, interrupts, sampling delay, electrical noise, calibration or physical power behavior. Writes to other registers have no effect, so not every third-party MPU driver is compatible. ESP32 and STM32 firmware execution remain unavailable. This model does not prove hardware accuracy.

Run offline smoke tests with `node --test tests/test_mpu6050.cjs tests/test_i2c_devices.cjs` and `python -m unittest discover -s tests -p test_mpu_project.py -v`. The existing project example integration suite (`python -m unittest discover -s tests -p test_projects.py -v`) compiles and runs each shipped experiment; it requires the configured AVR compiler/core and Node dependencies.

Review finding addressed: the practical workspace had no executable 6-axis IMU. Remaining risks: byte-level timing fidelity and lack of real hardware reference comparisons. Avoid treating visual catalogue coverage as firmware support.
