"""
kalibr2kimera.py
Converts a Kalibr camera-IMU calibration file to Kimera VIO parameters files.
Takes as input the camchain-imu.yaml file output by Kalibr,
and generates the files LeftCameraParams.yaml, and RightCameraParams.yaml which are used by Kimera.
Written by Brian H. Wang
May 2020
bhw45@cornell.edu
See also:
    https://github.com/MIT-SPARK/Kimera-VIO-ROS/issues/73

"""
import yaml
from collections import OrderedDict
import argparse

# Lets pyyaml write dictionaries in order. See stackoverflow link for reference.
def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)
setup_yaml()


def write_kimera_camera_yaml(output_filename, kalibr_cam, camera_id, camera_rate=30):
    """
    Parameters
    ----------
    kalibr_cam: dict
        Yaml dictionary from the Kalibr IMU & camera camchain file.
    camera_id: str
        Name of the camera, written to the "camera_id" field of the output yaml.
        Should be "left_cam" or "right_cam" depending if we're writing
        LeftCameraParams.yaml or RightCameraParams.yaml
    camera_rate: int
        Camera FPS, set to 30 by default
        (This is the correct rate for the Intel RealSense D435i)
        Needed as an input because the FPS is needed by Kimera but does not appear in the
        camchain file from Kalibr.
    Returns
    -------
    dict
        Yaml dict in Kimear format.
        Can be written to LeftCameraParmas.yaml or RightCameraParams.yaml
    """
    # Get camera extrinsics
    kimera_extrinsics = OrderedDict()
    # flatten extrinsics array to a list
    extrinsics_flattened = []
    for row in kalibr_cam["T_cam_imu"]:
        for x in row:
            extrinsics_flattened.append(x)
    kimera_extrinsics["T_BS"] = OrderedDict([("cols", 4),
                                             ("rows", 4),
                                             ("data", extrinsics_flattened)])

    # Get camera-specific parameters
    kimera_params = OrderedDict()
    kimera_params["rate_hz"] = camera_rate
    keys = ["resolution", "camera_model", "intrinsics", "distortion_model"]
    for key in keys: # copy over parameters that have the same name in Kalibr and Kimera files
        kimera_params[key] = kalibr_cam[key]
    kimera_params["distortion_coefficients"] = kalibr_cam["distortion_coeffs"]

    with open(output_filename, "w") as output_file:
        output_file.write("%YAML:1.0\n")
        output_file.write("# Converted from Kalibr format by kalibr2kimera.py\n")
        output_file.write("# General sensor definitions.\n")
        output_file.write("camera_id: %s\n" % camera_id)

        output_file.write("\n# Sensor extrinsics wrt. the body-frame.\n")
        yaml.dump(kimera_extrinsics, output_file)

        output_file.write("\n# Camera specific definitions.\n")
        yaml.dump(kimera_params, output_file)


if __name__ == "__main__":
    desc = "Converts a Kalibr IMU-camera calibration file to the Kimera camera parameters format."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("kalibr_filename", help="Camchain file from Kalibr IMU-camera calibration.")
    args = parser.parse_args()

    print("[INFO] Reading Kalibr parameters from %s" % args.kalibr_filename)
    with open(args.kalibr_filename, 'r') as kalibr_file:
        kalibr_yaml = yaml.load(kalibr_file)

    # Check that the Kalibr yaml file is from IMU-camera calibration (not just camera calibration)
    # If so, the yaml file should include an IMU-to-camera transformation matrix
    if not (kalibr_yaml['cam0'].has_key("T_cam_imu") and kalibr_yaml['cam1'].has_key("T_cam_imu")):
        raise KeyError("Could not find T_cam_imu in the Kalibr file. Camchain file must include calibration results from camera with IMU.")

    # Check which camera is on the left
    """
    NOTE ON LEFT AND RIGHT CAMERAS:
    There seems to be some inconsistency between how Realsense-ROS, Kalibr, and/or Kimera number the
    cameras and/or in how they define "left" and "right" -
    when I used /infra1/image_rect_raw as cam0 and /infra2/image_rect_raw as cam1 for Kalibr,
    then used cam0 for LeftCameraParams.yaml and cam1 for RightCameraParams.yaml,
    I got an error from Kimera saying the camera baseline was negative.
    
    I'm not 100% sure of the source of the mix-up, but this check should make sure that the left
    and right camera parameters work in Kimera with no issues.
    """
    print("[INFO] Determining left and right cameras.")
    cam0_x = kalibr_yaml['cam0']['T_cam_imu'][0][3]
    cam1_x = kalibr_yaml['cam1']['T_cam_imu'][0][3]
    print("cam0 is at x=%.4f, cam1 is at x=%.4f" % (cam0_x, cam1_x))
    if cam1_x < cam1_x:
        left = 'cam0'
        right = 'cam1'
    elif cam0_x > cam1_x:
        left = 'cam1'
        right = 'cam0'
    else:
        raise ValueError("Cameras are at same x-coordinate. Check calibration results for errors.")
    print("Left camera is %s, right camera is %s" % (left, right))


    print("[INFO] Converting left camera parameters...")
    kalibr_left_cam = kalibr_yaml[left]
    write_kimera_camera_yaml("LeftCameraParams.yaml", kalibr_left_cam, "left_cam")
    print("[INFO] Wrote left camera parameters.")

    print("[INFO] Converting right camera parameters...")
    kalibr_right_cam = kalibr_yaml[right]
    write_kimera_camera_yaml("RightCameraParams.yaml", kalibr_right_cam, "right_cam")
    print("[INFO] Wrote right camera parameters.")
