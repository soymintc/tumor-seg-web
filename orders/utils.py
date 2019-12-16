from keras_contrib.layers import GroupNormalization
from keras import backend as K

def dice_coefficient(y_true, y_pred, smooth=1e-8):
    y_true_flat, y_pred_flat = K.flatten(y_true), K.flatten(y_pred)
    dice_nom = 2 * K.sum(y_true_flat * y_pred_flat)
    dice_denom = K.sum(K.square(y_true_flat) + K.square(y_pred_flat))
#     dice_denom = K.sum(K.abs(y_true_flat) + K.abs(y_pred_flat))
    dice_coef = (dice_nom + smooth) / (dice_denom + smooth)
    return dice_coef

def dice_loss(y_true, y_pred, smooth=1e-8):
    dice_coef = dice_coefficient(y_true, y_pred, smooth)
    return 1 - dice_coef

custom_objects = {'dice_coefficient':dice_coefficient, 'dice_loss':dice_loss, 'GroupNormalization':GroupNormalization}
