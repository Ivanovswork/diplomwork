package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityChangePasswordBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ChangePasswordActivity : AppCompatActivity() {

    private lateinit var binding: ActivityChangePasswordBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChangePasswordBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        // Кнопка назад
        binding.btnBack.setOnClickListener {
            finish()
        }

        // Кнопка смены пароля
        binding.btnChangePassword.setOnClickListener {
            val oldPassword = binding.etOldPassword.text.toString().trim()
            val newPassword = binding.etNewPassword.text.toString().trim()
            val confirmPassword = binding.etConfirmPassword.text.toString().trim()

            if (oldPassword.isEmpty() || newPassword.isEmpty() || confirmPassword.isEmpty()) {
                Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (newPassword != confirmPassword) {
                Toast.makeText(this, "Новые пароли не совпадают", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val request = ChangePasswordRequest(oldPassword, newPassword, confirmPassword)
            api.changePassword("Token $token", request).enqueue(object : Callback<ChangePasswordResponse> {
                override fun onResponse(call: Call<ChangePasswordResponse>, response: Response<ChangePasswordResponse>) {
                    if (response.isSuccessful) {
                        Toast.makeText(this@ChangePasswordActivity, "Пароль изменен", Toast.LENGTH_SHORT).show()
                        finish()
                    } else {
                        Toast.makeText(this@ChangePasswordActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onFailure(call: Call<ChangePasswordResponse>, t: Throwable) {
                    Toast.makeText(this@ChangePasswordActivity, "Сеть недоступна: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        }
    }
}