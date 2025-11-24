import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function DashboardScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [gamification, setGamification] = useState({ points: 0, streak_days: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const storedUsername = await AsyncStorage.getItem('username');
      const token = await AsyncStorage.getItem('token');
      
      if (storedUsername) {
        setUsername(storedUsername);
      }

      const response = await axios.get(`${BACKEND_URL}/api/gamification`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGamification(response.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Sair',
      'Deseja realmente sair?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Sair',
          onPress: async () => {
            await AsyncStorage.clear();
            router.replace('/');
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Olá, {username}!</Text>
          <Text style={styles.subtitle}>Bem-vindo ao seu painel</Text>
        </View>
        <TouchableOpacity onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={28} color="#333" />
        </TouchableOpacity>
      </View>

      <View style={styles.gamificationCard}>
        <View style={styles.gamificationItem}>
          <Ionicons name="star" size={32} color="#FFD700" />
          <Text style={styles.gamificationValue}>{gamification.points}</Text>
          <Text style={styles.gamificationLabel}>Pontos</Text>
        </View>
        <View style={styles.gamificationDivider} />
        <View style={styles.gamificationItem}>
          <Ionicons name="flame" size={32} color="#FF5722" />
          <Text style={styles.gamificationValue}>{gamification.streak_days}</Text>
          <Text style={styles.gamificationLabel}>Dias Seguidos</Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.menuGrid}>
          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#4CAF50' }]}
            onPress={() => router.push('/add-expense')}
          >
            <Ionicons name="add-circle" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Adicionar Gasto</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#2196F3' }]}
          >
            <Ionicons name="list" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Ver Gastos</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#FF9800' }]}
          >
            <Ionicons name="cash" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Renda</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#9C27B0' }]}
          >
            <Ionicons name="card" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Dívidas</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#00BCD4' }]}
          >
            <Ionicons name="stats-chart" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Relatórios</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.menuCard, { backgroundColor: '#607D8B' }]}
          >
            <Ionicons name="settings" size={40} color="#fff" />
            <Text style={styles.menuCardText}>Configurações</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 24,
    paddingTop: 48,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  gamificationCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 12,
    padding: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  gamificationItem: {
    flex: 1,
    alignItems: 'center',
  },
  gamificationValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  gamificationLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  gamificationDivider: {
    width: 1,
    backgroundColor: '#e0e0e0',
    marginHorizontal: 16,
  },
  content: {
    flex: 1,
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
  },
  menuCard: {
    width: '45%',
    aspectRatio: 1,
    margin: 8,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  menuCardText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    textAlign: 'center',
  },
});
