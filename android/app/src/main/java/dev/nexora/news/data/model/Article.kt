package dev.nexora.news.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Article(
    val id: String = "",
    val title: String = "",
    val summary: String = "",
    val body: List<String> = emptyList(),
    val source: String = "",
    val category: String = "",
    @SerialName("category_label") val categoryLabel: String = "",
    val url: String = "",
    val image: String? = null,
    @SerialName("published_at") val publishedAt: String = "",
    @SerialName("read_minutes") val readMinutes: Int = 2,
)

@Serializable
data class Category(
    val id: String = "",
    val label: String = "",
    val count: Int = 0,
)

@Serializable
data class Feed(
    val articles: List<Article> = emptyList(),
    val total: Int = 0,
    @SerialName("updated_at") val updatedAt: String? = null,
    val categories: List<Category> = emptyList(),
    val live: Boolean = false,
)
