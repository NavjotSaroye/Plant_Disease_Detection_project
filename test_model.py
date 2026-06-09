from tensorflow.keras.models import load_model

model = load_model("model/best_model.h5")

model.summary()