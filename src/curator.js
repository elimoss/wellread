import fs from 'fs/promises';

export class ContentCurator {
  async loadTopics(topicsFile = 'topics.txt') {
    const content = await fs.readFile(topicsFile, 'utf-8');
    return content
      .split('\n')
      .map(line => line.trim().toLowerCase())
      .filter(line => line && !line.startsWith('#'));
  }

  calculateRelevanceScore(item, topics) {
    let score = 0;
    const searchText = `${item.title || ''} ${item.description || ''} ${item.content || ''}`.toLowerCase();

    for (const topic of topics) {
      // Exact phrase match
      if (searchText.includes(topic)) {
        score += 10;
      }

      // Individual word matches
      const topicWords = topic.split(/\s+/);
      for (const word of topicWords) {
        if (word.length > 3 && searchText.includes(word)) {
          score += 2;
        }
      }
    }

    return score;
  }

  curateItems(items, topics, minScore = 1) {
    const scoredItems = items.map(item => ({
      ...item,
      relevanceScore: this.calculateRelevanceScore(item, topics)
    }));

    return scoredItems
      .filter(item => item.relevanceScore >= minScore)
      .sort((a, b) => b.relevanceScore - a.relevanceScore);
  }

  groupByRelevance(curatedItems) {
    const highRelevance = curatedItems.filter(item => item.relevanceScore >= 20);
    const mediumRelevance = curatedItems.filter(item => item.relevanceScore >= 10 && item.relevanceScore < 20);
    const lowRelevance = curatedItems.filter(item => item.relevanceScore > 0 && item.relevanceScore < 10);

    return {
      high: highRelevance,
      medium: mediumRelevance,
      low: lowRelevance
    };
  }
}
