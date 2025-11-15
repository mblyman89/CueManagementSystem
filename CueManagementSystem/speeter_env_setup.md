# Create with Python 3.8
conda create -n spleeter_arm python=3.8 -y
conda activate spleeter_arm

# Install TensorFlow for Apple Silicon
pip install tensorflow-macos==2.9.0

# Install Spleeter
pip install spleeter