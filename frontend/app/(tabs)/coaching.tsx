import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
  ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useSounds } from '../../hooks/useSounds';
import { SkeletonList } from '../../components/SkeletonLoader';
import { useHaptics } from '../../hooks/useHaptics';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

const QUICK_QUESTIONS_KEYS = [
  { icon: 'trending-up', key: 'q1', color: '#4CAF50' },
  { icon: 'cash', key: 'q2', color: '#FF9800' },
  { icon: 'business', key: 'q3', color: '#2196F3' },
  { icon: 'school', key: 'q4', color: '#9C27B0' },
  { icon: 'card', key: 'q5', color: '#1E88E5' },
  { icon: 'trophy', key: 'q6', color: '#FFD700' },
];

interface ChatMessage {
  id: string;
  type: 'user' | 'coach';
  text: string;
  timestamp: string;
}

export default function Coaching() {
  const { token, user } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const { play } = useSounds();
  const { trigger: haptic } = useHaptics();
  const scrollRef = useRef<ScrollView>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  // Load history
  const loadHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/api/coaching/history`, { headers });
      const history = (res.data.history || []).reverse();
      const msgs: ChatMessage[] = [];
      history.forEach((h: any) => {
        msgs.push({
          id: `q-${h.id}`,
          type: 'user',
          text: h.question,
          timestamp: h.created_at,
        });
        msgs.push({
          id: `a-${h.id}`,
          type: 'coach',
          text: h.response,
          timestamp: h.created_at,
        });
      });
      setMessages(msgs);
    } catch (e) { console.error(e); }
    finally { setHistoryLoaded(true); }
  }, [token]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 300);
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;
    play('click');

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      text: question.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await axios.post(`${API}/api/coaching/advice`, { question: question.trim() }, { headers });
      play('notification');
      const coachMsg: ChatMessage = {
        id: `coach-${Date.now()}`,
        type: 'coach',
        text: res.data.advice,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, coachMsg]);
    } catch (e: any) {
      play('error');
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        type: 'coach',
        text: t('coaching.errorMsg') || 'Sorry, technical issues. Try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <View style={s.headerCenter}>
          <View style={s.coachAvatar}>
            <Ionicons name="sparkles" size={20} color="#FFD700" />
          </View>
          <View>
            <Text style={s.headerTitle}>{t('coaching.title')}</Text>
            <Text style={s.headerSub}>{t('coaching.subtitle')}</Text>
          </View>
        </View>
        <View style={s.onlineDot} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
        keyboardVerticalOffset={0}
      >
        {/* Chat Messages */}
        <ScrollView
          ref={scrollRef}
          style={s.chatArea}
          contentContainerStyle={s.chatContent}
          onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
        >
          {/* Welcome message */}
          {messages.length === 0 && historyLoaded && (
            <View style={s.welcomeContainer}>
              <View style={s.welcomeIcon}>
                <Ionicons name="sparkles" size={40} color="#FFD700" />
              </View>
              <Text style={s.welcomeTitle}>{t('coaching.welcome')}, {user?.username || 'Jogador'}!</Text>
              <Text style={s.welcomeText}>
                {t('coaching.welcomeText')}
              </Text>
              <Text style={s.welcomeHint}>{t('coaching.welcomeHint')}</Text>

              <View style={s.quickGrid}>
                {QUICK_QUESTIONS_KEYS.map((q, i) => (
                  <TouchableOpacity
                    key={i}
                    style={s.quickCard}
                    onPress={() => sendMessage(t(`coaching.${q.key}`))}
                  >
                    <Ionicons name={q.icon as any} size={20} color={q.color} />
                    <Text style={s.quickText}>{t(`coaching.${q.key}`)}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Messages */}
          {messages.map(msg => (
            <View key={msg.id} style={[s.msgRow, msg.type === 'user' && s.msgRowUser]}>
              {msg.type === 'coach' && (
                <View style={s.coachAvatarSmall}>
                  <Ionicons name="sparkles" size={14} color="#FFD700" />
                </View>
              )}
              <View style={[s.msgBubble, msg.type === 'user' ? s.userBubble : s.coachBubble]}>
                <Text style={[s.msgText, msg.type === 'user' && s.userMsgText]}>{msg.text}</Text>
              </View>
            </View>
          ))}

          {/* Typing indicator */}
          {loading && (
            <View style={s.msgRow}>
              <View style={s.coachAvatarSmall}>
                <Ionicons name="sparkles" size={14} color="#FFD700" />
              </View>
              <SkeletonList count={4} style={{ padding: 16 }} />
            </View>
          )}

          {/* Quick questions after first response */}
          {messages.length > 0 && !loading && (
            <View style={s.quickActionsRow}>
              {QUICK_QUESTIONS_KEYS.slice(0, 3).map((q, i) => (
                <TouchableOpacity key={i} style={s.quickPill} onPress={() => sendMessage(t(`coaching.${q.key}`))}>
                  <Text style={s.quickPillText}>{t(`coaching.${q.key}`)}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </ScrollView>

        {/* Input Area */}
        <View style={s.inputArea}>
          <TextInput
            style={s.input}
            placeholder={t('coaching.placeholder')}
            placeholderTextColor="#555"
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => sendMessage(inputText)}
            editable={!loading}
            multiline
          />
          <TouchableOpacity
            style={[s.sendBtn, (!inputText.trim() || loading) && s.sendBtnDisabled]}
            onPress={() => sendMessage(inputText)}
            disabled={!inputText.trim() || loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#000" />
            ) : (
              <Ionicons name="send" size={20} color="#000" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  // Header
  header: { flexDirection: 'row', alignItems: 'center', padding: 14, borderBottomWidth: 1, borderBottomColor: '#2a2a2a', gap: 10 },
  backBtn: { padding: 4 },
  headerCenter: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 },
  coachAvatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#FFD70020', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#FFD70050' },
  headerTitle: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  headerSub: { color: '#888', fontSize: 11 },
  onlineDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#4CAF50' },
  // Chat
  chatArea: { flex: 1 },
  chatContent: { padding: 16, paddingBottom: 8 },
  // Welcome
  welcomeContainer: { alignItems: 'center', paddingVertical: 20 },
  welcomeIcon: { width: 72, height: 72, borderRadius: 36, backgroundColor: '#FFD70015', justifyContent: 'center', alignItems: 'center', marginBottom: 16, borderWidth: 2, borderColor: '#FFD70030' },
  welcomeTitle: { color: '#fff', fontSize: 22, fontWeight: 'bold', marginBottom: 8 },
  welcomeText: { color: '#aaa', fontSize: 14, textAlign: 'center', lineHeight: 20, marginBottom: 6, paddingHorizontal: 20 },
  welcomeHint: { color: '#666', fontSize: 12, marginBottom: 16 },
  quickGrid: { width: '100%', gap: 8 },
  quickCard: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14 },
  quickText: { color: '#ccc', fontSize: 14 },
  // Messages
  msgRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 12, gap: 8 },
  msgRowUser: { justifyContent: 'flex-end' },
  coachAvatarSmall: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#FFD70020', justifyContent: 'center', alignItems: 'center' },
  msgBubble: { maxWidth: '80%', borderRadius: 16, padding: 12 },
  userBubble: { backgroundColor: '#1E88E5', borderBottomRightRadius: 4 },
  coachBubble: { backgroundColor: '#2a2a2a', borderBottomLeftRadius: 4 },
  msgText: { color: '#ddd', fontSize: 14, lineHeight: 20 },
  userMsgText: { color: '#fff' },
  typingBubble: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  typingText: { color: '#888', fontSize: 13 },
  // Quick actions after messages
  quickActionsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4, marginBottom: 8 },
  quickPill: { backgroundColor: '#2a2a2a', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 8, borderWidth: 1, borderColor: '#3a3a3a' },
  quickPillText: { color: '#aaa', fontSize: 12 },
  // Input
  inputArea: { flexDirection: 'row', alignItems: 'flex-end', padding: 12, borderTopWidth: 1, borderTopColor: '#2a2a2a', gap: 8 },
  input: { flex: 1, backgroundColor: '#2a2a2a', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, color: '#fff', fontSize: 15, maxHeight: 100, borderWidth: 1, borderColor: '#3a3a3a' },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#FFD700', justifyContent: 'center', alignItems: 'center' },
  sendBtnDisabled: { opacity: 0.4 },
});
