import React, { useRef, ReactNode } from 'react';
import { Animated, TouchableOpacity, ViewStyle } from 'react-native';

interface AnimatedPressProps {
  onPress?: () => void;
  style?: ViewStyle | ViewStyle[];
  children: ReactNode;
  disabled?: boolean;
  scaleDown?: number;
}

export default function AnimatedPress({ onPress, style, children, disabled, scaleDown = 0.96 }: AnimatedPressProps) {
  const scale = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scale, { toValue: scaleDown, useNativeDriver: true, speed: 50, bounciness: 4 }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scale, { toValue: 1, useNativeDriver: true, speed: 50, bounciness: 4 }).start();
  };

  return (
    <TouchableOpacity
      activeOpacity={0.9}
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled}
    >
      <Animated.View style={[style as any, { transform: [{ scale }] }]}>
        {children}
      </Animated.View>
    </TouchableOpacity>
  );
}
