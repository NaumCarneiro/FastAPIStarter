import { Stack } from 'expo-router';

export default function Layout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="master-login" />
      <Stack.Screen name="profile" />
      <Stack.Screen name="dashboard" />
      <Stack.Screen name="admin-panel" />
      <Stack.Screen name="add-expense" />
    </Stack>
  );
}
