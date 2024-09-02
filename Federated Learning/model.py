import numpy as np
from tensorflow.keras.layers import Input, LSTM, GRU, Bidirectional, Dense
from tensorflow.keras.models import Model
from config import EPOCHS, WINDOW_SIZE, UNITS, DATA_DIR, NUM_CLIENTS, SERVER_ADDRESS

def LSTM(input_shape, UNITS):
    inputs = Input(shape=input_shape)
    lstm_out = LSTM(UNITS)(inputs)
    output = Dense(1)(lstm_out)
    model = Model(inputs=inputs, outputs=output)
    return model


def GRU(input_shape, UNITS):
    inputs = Input(shape=input_shape)
    gru_out = GRU(UNITS)(inputs)
    output = Dense(1)(gru_out)
    model = Model(inputs=inputs, outputs=output)
    return model


def BiLSTM(input_shape, UNITS):
    inputs = Input(shape=input_shape)
    bilstm_out = Bidirectional(LSTM(UNITS))(inputs)
    output = Dense(1)(bilstm_out)
    model = Model(inputs=inputs, outputs=output)
    return model


def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)
