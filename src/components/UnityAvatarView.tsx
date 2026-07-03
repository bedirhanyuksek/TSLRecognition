import React from 'react';
import {
  Platform,
  requireNativeComponent,
  StyleProp,
  View,
  ViewStyle,
} from 'react-native';

type Props = {
  style?: StyleProp<ViewStyle>;
};

const NativeUnityAvatarView =
  Platform.OS === 'android'
    ? requireNativeComponent<Props>('TidUnityAvatarView')
    : null;

export function UnityAvatarView({style}: Props) {
  if (!NativeUnityAvatarView) {
    return <View style={style} />;
  }

  return <NativeUnityAvatarView style={style} />;
}
