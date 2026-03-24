package com.example.myapplication

import retrofit2.Call
import retrofit2.http.*

// Модели данных
data class RegisterRequest(
    val name: String,
    val email: String,
    val password: String,
    val password_confirm: String
)

data class RegisterResponse(
    val status: String? = null,
    val errors: Any? = null
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val user: User? = null
)

data class User(
    val id: Int,
    val name: String,
    val email: String,
    val is_account_active: Boolean,
    val subscription_type: String
)

// Интерфейс для вызовов API
interface DjangoApi {
    @POST("api/users/register/")
    fun register(@Body body: RegisterRequest): Call<RegisterResponse>

    @POST("api/users/login/")
    fun login(@Body body: LoginRequest): Call<LoginResponse>
}