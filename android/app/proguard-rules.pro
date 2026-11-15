# kotlinx.serialization keeps generated serializers via @Serializable metadata.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**

-keepclassmembers class dev.nexora.news.data.model.** {
    *** Companion;
}
-keepclasseswithmembers class dev.nexora.news.data.model.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response
