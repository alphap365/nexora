package dev.nexora.news.data

import dev.nexora.news.data.model.Article
import dev.nexora.news.data.model.Feed
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface NewsApi {

    @GET("api/articles")
    suspend fun feed(
        @Query("category") category: String = "top",
        @Query("q") query: String? = null,
        @Query("limit") limit: Int = 60,
    ): Feed

    @GET("api/articles/{id}")
    suspend fun article(@Path("id") id: String): Article
}
