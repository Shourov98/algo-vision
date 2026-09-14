export const problemTopics = ["All", "Arrays", "Hashing", "Strings", "Trees"] as const;
export type ProblemTopic = Exclude<(typeof problemTopics)[number], "All">;
export interface ProblemSummary {
  slug: string;
  title: string;
  description: string;
  difficulty: "Easy" | "Medium" | "Hard";
  topic: ProblemTopic;
}
export const problems: readonly ProblemSummary[] = [
  {
    slug: "two-sum",
    title: "Two Sum",
    description: "Find two values that add up to a target.",
    difficulty: "Easy",
    topic: "Arrays",
  },
  {
    slug: "valid-parentheses",
    title: "Valid Parentheses",
    description: "Check whether nested brackets are balanced.",
    difficulty: "Easy",
    topic: "Strings",
  },
  {
    slug: "group-anagrams",
    title: "Group Anagrams",
    description: "Group words with the same character counts.",
    difficulty: "Medium",
    topic: "Hashing",
  },
  {
    slug: "validate-bst",
    title: "Validate Binary Search Tree",
    description: "Verify strict ordering across every tree branch.",
    difficulty: "Medium",
    topic: "Trees",
  },
];
