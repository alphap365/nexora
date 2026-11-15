package dev.nexora.news.data

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import dev.nexora.news.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

/**
 * Minimal manual dependency graph — no Hilt in a demo this size.
 * Swap [NewsApi] for a fake in tests or previews.
 */
object ServiceLocator {

    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        isLenient = true
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val repository: NewsRepository = NewsRepository(retrofit.create(NewsApi::class.java))
}
