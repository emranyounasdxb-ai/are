import { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import Animated, {
  Easing,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";

export default function MobileFoundationScreen() {
  const progress = useSharedValue(0);
  const entranceStyle = useAnimatedStyle(() => ({
    opacity: 0.92 + progress.value * 0.08,
    transform: [{ translateY: (1 - progress.value) * 12 }],
  }));

  useEffect(() => {
    progress.value = withTiming(1, {
      duration: 420,
      easing: Easing.out(Easing.cubic),
      reduceMotion: ReduceMotion.System,
    });
  }, [progress]);

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.safeArea}>
        <Animated.View style={[styles.content, entranceStyle]}>
          <Text accessibilityRole="header" style={styles.title}>
            ALIYAS Real Estate
          </Text>
          <Text style={styles.heading}>Mobile Foundation</Text>
          <Text style={styles.platforms}>Android &amp; iOS</Text>
          <Text style={styles.description}>The native workspace is ready.</Text>
        </Animated.View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F8F6F2",
  },
  safeArea: {
    flex: 1,
  },
  content: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
  },
  title: {
    color: "#17110E",
    fontSize: 28,
    fontWeight: "600",
    textAlign: "center",
  },
  heading: {
    color: "#5A3827",
    fontSize: 20,
    fontWeight: "600",
    textAlign: "center",
  },
  platforms: {
    color: "#17110E",
    fontSize: 16,
    textAlign: "center",
  },
  description: {
    color: "#625850",
    fontSize: 16,
    textAlign: "center",
  },
});
