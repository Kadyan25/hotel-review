// One fixed color per topic, reused everywhere a topic appears (insight
// bars, review-card tags, chart legends) so a topic is visually
// recognizable at a glance instead of everything being the same 1-2 hues.
export const TOPIC_COLORS: Record<string, string> = {
  cleanliness: "#0ea5e9", // sky
  checkin_experience: "#8b5cf6", // violet
  staff_behaviour: "#ec4899", // pink
  noise: "#f97316", // orange
  facilities: "#14b8a6", // teal
  location: "#6366f1", // indigo
  room_condition: "#f59e0b", // amber
  value_for_money: "#10b981", // emerald
  other: "#64748b", // slate
};

export function topicColor(topic: string): string {
  return TOPIC_COLORS[topic] ?? TOPIC_COLORS.other;
}

export function formatTopic(topic: string): string {
  return topic.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}
