import { View, Text, FlatList } from 'react-native';
import React, { useEffect, useState } from 'react';
import { apiFetch } from "@/services/api";

export default function App() {
  const [players, setPlayers] = useState([]);

  useEffect(() => {
    apiFetch('/nfl/players')
      .then(r => r.json())
      .then(d => setPlayers(d.players))
      .catch(console.error);
  }, []);

  return (
    <View style={{ padding: 16 }}>
      <Text style={{ fontSize: 18 }}>Fantasy Players</Text>
      <FlatList
        data={players}
        keyExtractor={p => p}
        renderItem={({ item }) => <Text>{item}</Text>}
      />
    </View>
  );
}