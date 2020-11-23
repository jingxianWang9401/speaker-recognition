
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, MaxoutDense, GRU
from keras.models import load_model
from keras.layers.normalization import BatchNormalization
from keras import Model
from keras.layers.core import Reshape,Masking,Lambda,Permute
from keras.layers import Input,Dense,Flatten
import keras
from keras.layers import Convolution2D, MaxPooling2D
from keras.layers.wrappers import TimeDistributed
from keras.optimizers import SGD, Adam
from keras.callbacks import ModelCheckpoint, TensorBoard
import random

import keras.backend as K
import numpy as np
import librosa
import python_speech_features as psf
import os
import tensorflow as tf

# ָ��GPU
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="1"
# ָ��ռ���ڴ��С
config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.43  # ռ��GPU43%���Դ�
K.set_session(tf.Session(config=config))


filePath = "E:/speaker_recognition_demo/1dVectorSpeakerRecognition-master/kersaSoftmax/dataset_all"
# filePath = "data/test"
nClass = len(os.listdir(filePath))


def getwavPathAndwavLabel(filePath):
    wavPath = []
    wavLabel = []
    testPath = []
    testLable = []
    files = os.listdir(filePath)
    lab = 0
    for file in files:
        wav = os.listdir(filePath+"/"+file)
        for j in range(len(wav)):
            fileType = wav[j].split(".")[1]
            if float(j)>0.01*len(wav):
                if fileType=="wav":
                    wavLabel.append(lab)
                    wavPath.append(filePath+"/"+file+"/"+wav[j])
            else:
                testLable.append(lab)
                testPath.append(filePath + "/" + file + "/" + wav[j])
        lab += 1
    return wavPath, wavLabel, testPath, testLable


wavPath, wavLabel, testPath, testLabel = getwavPathAndwavLabel(filePath)
print("trainWavPath: ", len(wavPath))
print("testWavPath: ", len(testPath))
# '''������ͬ��˳������ļ�'''
# cc = list(zip(wavPath, wavLabel))
# random.shuffle(cc)
# wavPath[:], wavLabel[:] = zip(*cc)
# testPath = [len(wavPath)-1000 : len(wavPath)-1]
# testLabel = [len(wavPath)-1000 : len(wavPath)-1]

def getBW(batchSize=2, second=3, sampleRate=16000):
    """
    :param batchSize: һ�����δ�С
    :param second: ��Ƶ�ĳ��ȣ�Ĭ��3.5s,��λΪsec
    :param sampleRate: ������
    :return:��������  �� ��ǩ
    """
    count = 0
    while True:

        '''������ͬ��˳������ļ�'''
        cc = list(zip(wavPath, wavLabel))
        random.shuffle(cc)
        wavPath[:], wavLabel[:] = zip(*cc)
        x = []
        y = []
        count = 0
        for index, wav in enumerate(wavPath):
            if count == batchSize:
                X = x
                Y = y
                # print(np.array(x).shape)
                X = np.array(X)  # (2, 64, 299, 3)
                Y = np.array(Y)
                Y = keras.utils.to_categorical(y, nClass)
                # print()
                x = []
                y = []
                count = 0

                yield [X, Y]
                # print(X.shape)
                # print(Y.shape)

            else:
                signal, srate = librosa.load(wav, sr=sampleRate)
                # ����������
                if len(signal) < 3 * 16000:
                    continue
                # ��һ��
                signal = signal / (max(np.abs(np.min(signal)), np.max(signal)))

                # �ж��Ƿ񳬹����룬
                # ����������ض�
                if len(signal) >= 3 * srate:
                    signal = signal[0:int(3 * srate)]
                # �������������0
                else:
                    signal = signal.tolist()
                    for j in range(3 * srate - len(signal)):
                        signal.append(0)
                    signal = np.array(signal)

                feat = psf.logfbank(signal[0:16000*3],samplerate=16000, nfilt=64)
                feat1 = psf.delta(feat, 1)
                feat2 = psf.delta(feat, 2)
                feat = feat.T[:, :, np.newaxis]
                feat1 = feat1.T[:, :, np.newaxis]
                feat2 = feat2.T[:, :, np.newaxis]
                fBank = np.concatenate((feat, feat1, feat2), axis=2)
                x.append(fBank)
                y.append(wavLabel[index])



                count +=1

def getTestBW(batchSize=2, second=3, sampleRate=16000):
    """
    :param batchSize: һ�����δ�С
    :param second: ��Ƶ�ĳ��ȣ�Ĭ��3.5s,��λΪsec
    :param sampleRate: ������
    :return:��������  �� ��ǩ
    """
    count = 0
    while True:

        '''������ͬ��˳������ļ�'''
        cc = list(zip(testPath, testLabel))
        random.shuffle(cc)
        testPath[:], testLabel[:] = zip(*cc)
        x = []
        y = []
        count = 0
        for index, wav in enumerate(testPath):
            if count == batchSize:
                X = x
                Y = y
                # print(np.array(x).shape)
                X = np.array(X)  # (2, 64, 299, 3)
                Y = np.array(Y)
                Y = keras.utils.to_categorical(y, nClass)
                # print()
                x = []
                y = []
                count = 0

                yield [X, Y]
                # print(X.shape)
                # print(Y.shape)

            else:
                signal, srate = librosa.load(wav, sr=sampleRate)
                if len(signal) <3*16000:
                    continue
                # ��һ��
                signal = signal / (max(np.abs(np.min(signal)), np.max(signal)))

                # �ж��Ƿ񳬹����룬
                # ����������ض�
                if len(signal) >= 3 * srate:
                    signal = signal[0:int(3 * srate)]
                # �������������0
                else:
                    signal = signal.tolist()
                    for j in range(3 * srate - len(signal)):
                        signal.append(0)
                    signal = np.array(signal)
                # print(len(signal))



                # feat = librosa.feature.mfcc(signal[0:16000*3], sr=16000, n_mfcc=64)
                feat = psf.logfbank(signal[0:16000*3],samplerate=16000, nfilt=64)
                # print("feat: ", feat.shape)
                feat1 = psf.delta(feat, 1)
                feat2 = psf.delta(feat, 2)
                feat = feat.T[:, :, np.newaxis]
                feat1 = feat1.T[:, :, np.newaxis]
                feat2 = feat2.T[:, :, np.newaxis]
                fBank = np.concatenate((feat, feat1, feat2), axis=2)
                x.append(fBank)
                y.append(testLabel[index])
                count +=1


if __name__ =="__main__":

    batchSize = 32
    # ����˸���
    nFilter = 64
    # �ػ���Ĵ�С
    poolSize = [2, 2]
    # �ػ��㲽��
    strideSize = [2, 2]
    # ����˵Ĵ�С
    kernelSize = [5, 5]
    model = Sequential()
    model.add(Convolution2D(nFilter, (kernelSize[0], kernelSize[1]),
                            padding='same',
                            strides=(strideSize[0], strideSize[1]),
                            input_shape=(64, None, 3), name="cov1",
                            kernel_regularizer=keras.regularizers.l2()))
    # model.add(MaxPooling2D(pool_size=(poolSize[0], poolSize[1]), strides=(strideSize[0], strideSize[1]), padding="same", name="pool1"))

    # �������ά�Ȱ��ո���ģʽ��������
    model.add(Permute((2,1,3),name='permute'))
    # �ð�װ�����԰�һ����Ӧ�õ������ÿһ��ʱ�䲽��,GRU��Ҫ
    model.add(TimeDistributed(Flatten(),name='timedistrib'))

    # ����GRU
    model.add(GRU(units=1024, return_sequences=True, name="gru1"))
    model.add(GRU(units=1024, return_sequences=True, name="gru2"))
    model.add(GRU(units=1024, return_sequences=True, name="gru3"))

    # temporal average
    def temporalAverage(x):
        return K.mean(x, axis=1)
    model.add(Lambda(temporalAverage, name="temporal_average"))

    # affine
    model.add(Dense(units=512, name="dense1"))

    # length normalization
    def lengthNormalization(x):
        return K.l2_normalize(x, axis=-1)
    model.add(Lambda(lengthNormalization, name="ln"))

    model.add(Dense(units=nClass ,name="dense2"))
    model.add(Activation("softmax"))

    sgd = Adam(lr=0.00001)

    model.compile(loss='categorical_crossentropy',
                  optimizer=sgd, metrics=['accuracy'])

    model.fit_generator(getBW(batchSize, sampleRate=16000),steps_per_epoch = len(wavLabel)//batchSize, epochs=15,
                        validation_data=getTestBW(100),
                        validation_steps=5,
                        callbacks=[
                            # ÿ��ѵ������һ��ģ��
                            ModelCheckpoint("{epoch:02d}e-val_acc_{val_acc:.2f}.hdf5",
                                            monitor='loss', verbose=1, save_best_only=False, mode='min', period=1),
                            # �����ָ�겻���ʱ��ѧϰ��lr = lr *0.1
                            keras.callbacks.ReduceLROnPlateau(monitor='loss', factor=0.1, patience=10,
                                                              verbose=0, mode='min', epsilon=0.0001, cooldown=0,
                                                              min_lr=0),
                            TensorBoard(log_dir="./log1"),
                            # keras.callbacks.EarlyStopping(monitor='loss', patience=50, verbose=2)
    ])
