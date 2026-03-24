package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityHomeBinding

class HomeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHomeBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Получаем email из SharedPreferences
        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        val email = prefs.getString("email", "user@example.com")
        binding.tvUserEmail.text = email

        // Временная заглушка для имени
        binding.tvWelcome.text = "Привет, Читатель!"

        // Кнопка "Продолжить чтение"
        binding.btnContinueReading.setOnClickListener {
            Toast.makeText(this, "Скоро здесь будет список книг", Toast.LENGTH_SHORT).show()
        }

        // Кнопка "Мои книги"
        binding.btnMyBooks.setOnClickListener {
            Toast.makeText(this, "Скоро здесь будет список книг", Toast.LENGTH_SHORT).show()
        }

        // Кнопка "Статистика"
        binding.btnStats.setOnClickListener {
            Toast.makeText(this, "Скоро здесь будет статистика", Toast.LENGTH_SHORT).show()
        }

        // Кнопка выхода
        binding.btnLogout.setOnClickListener {
            // Очищаем сохраненные данные
            getSharedPreferences("auth", MODE_PRIVATE).edit().clear().apply()
            // Переходим на экран логина
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
        }
    }
}