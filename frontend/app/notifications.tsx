import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { SkeletonList } from '../components/SkeletonLoader';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Notifications() {
  const router = useRouter();
  const { token } = useAuth();
  const { t } = useLanguage();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const res = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/notifications`, { headers });
      setNotifications(res.data.notifications);
      setUnreadCount(res.data.unread_count);
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, [token]);

  useEffect(() => { loadData(); }, []);

  const markAllRead = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/notifications/read`, { notification_id: 'all' }, { headers });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (e) { console.error(e); }
  };

  const getIcon = (type: string, icon?: string): string => {
    if (icon) return icon;
    switch (type) {
      case 'achievement': return 'trophy';
      case 'purchase': return 'cart';
      case 'revenue': return 'cash';
      case 'ranking': return 'podium';
      default: return 'notifications';
    }
  };

  const getColor = (type: string): string => {
    switch (type) {
      case 'achievement': return '#FFD700';
      case 'purchase': return '#4CAF50';
      case 'revenue': return '#FF9800';
      case 'ranking': return '#2196F3';
      default: return '#888';
    }
  };

  const timeAgo = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'now';
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  };

  if (loading) return <SafeAreaView style={s.container}><SkeletonList count={5} style={{ padding: 16, paddingTop: 60 }} /></SafeAreaView>;

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>{t('notifications.title')}</Text>
        {unreadCount > 0 && (
          <TouchableOpacity onPress={markAllRead} style={s.markAllBtn}>
            <Text style={s.markAllText}>{t('notifications.markAllRead')}</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        style={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor="#4CAF50" />}
      >
        {notifications.length === 0 ? (
          <View style={s.empty}>
            <Ionicons name="notifications-off" size={48} color="#555" />
            <Text style={s.emptyText}>{t('notifications.empty')}</Text>
          </View>
        ) : (
          notifications.map((n) => (
            <View key={n.id} style={[s.card, !n.read && s.cardUnread]}>
              <View style={[s.iconCircle, { backgroundColor: getColor(n.type) + '22' }]}>
                <Ionicons name={getIcon(n.type, n.icon) as any} size={22} color={getColor(n.type)} />
              </View>
              <View style={s.info}>
                <Text style={s.notifTitle}>{n.title}</Text>
                <Text style={s.notifMsg}>{n.message}</Text>
              </View>
              <Text style={s.time}>{timeAgo(n.created_at)}</Text>
              {!n.read && <View style={s.unreadDot} />}
            </View>
          ))
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  back: { padding: 4 },
  title: { flex: 1, fontSize: 22, fontWeight: 'bold', color: '#fff' },
  markAllBtn: { padding: 8 },
  markAllText: { color: '#4CAF50', fontSize: 13, fontWeight: '600' },
  list: { flex: 1, padding: 16 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1a1a2e', borderRadius: 14, padding: 14, marginBottom: 8, gap: 12 },
  cardUnread: { borderLeftWidth: 3, borderLeftColor: '#4CAF50' },
  iconCircle: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  info: { flex: 1 },
  notifTitle: { fontSize: 14, fontWeight: 'bold', color: '#fff' },
  notifMsg: { fontSize: 13, color: '#aaa', marginTop: 2 },
  time: { fontSize: 11, color: '#666' },
  unreadDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#4CAF50' },
  empty: { alignItems: 'center', paddingTop: 80 },
  emptyText: { color: '#666', fontSize: 16, marginTop: 12 },
});
