package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityLoginBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private lateinit var api: DjangoApi

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Настройка Retrofit
        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        // Кнопка "Войти"
        binding.btnLogin.setOnClickListener {
            val email = binding.etLoginEmail.text.toString().trim()
            val password = binding.etLoginPassword.text.toString().trim()

            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Заполните email и пароль", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val request = LoginRequest(email, password)
            api.login(request).enqueue(object : Callback<LoginResponse> {
                override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                    if (response.isSuccessful && response.body() != null) {
                        val loginResponse = response.body()!!
                        val token = loginResponse.token
                        val user = loginResponse.user

                        // Сохраняем данные пользователя
                        getSharedPreferences("auth", MODE_PRIVATE).edit().apply {
                            putString("token", token)
                            putString("email", email)
                            putInt("user_id", user?.id ?: 0)
                            putString("user_name", user?.name ?: email.split("@")[0])
                            apply()
                        }

                        Toast.makeText(this@LoginActivity, "Вход выполнен", Toast.LENGTH_SHORT).show()
                        startActivity(Intent(this@LoginActivity, HomeActivity::class.java))
                        finish()
                    } else {
                        when (response.code()) {
                            401 -> Toast.makeText(this@LoginActivity, "Неверный email или пароль", Toast.LENGTH_LONG).show()
                            403 -> Toast.makeText(this@LoginActivity, "Подтвердите email перед входом", Toast.LENGTH_LONG).show()
                            else -> Toast.makeText(this@LoginActivity, "Ошибка: ${response.code()}", Toast.LENGTH_LONG).show()
                        }
                    }
                }

                override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                    Toast.makeText(this@LoginActivity, "Сеть недоступна: ${t.localizedMessage}", Toast.LENGTH_LONG).show()
                }
            })
        }

        // Переход на экран регистрации
        binding.tvGoToRegister.setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }
    }
}