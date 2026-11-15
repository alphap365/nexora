package dev.nexora.news.data

import dev.nexora.news.data.model.Article
import dev.nexora.news.data.model.Feed

class NewsRepository(private val api: NewsApi) {

    suspend fun feed(category: String, query: String): Result<Feed> = runCatching {
        api.feed(category = category, query = query.trim().ifBlank { null })
    }

    suspend fun article(id: String): Result<Article> = runCatching {
        api.article(id)
    }
}
