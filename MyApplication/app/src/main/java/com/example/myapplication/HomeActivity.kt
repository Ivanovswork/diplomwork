package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityHomeBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class HomeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHomeBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private val handler = Handler(Looper.getMainLooper())
    private var requestsCountRunnable: Runnable? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""
        val email = prefs.getString("email", "user@example.com")
        val userName = prefs.getString("user_name", "Читатель")

        binding.tvWelcome.text = "Привет, $userName!"
        binding.tvUserEmail.text = email

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.btnProfile.setOnClickListener {
            startActivity(Intent(this, ProfileActivity::class.java))
        }

        binding.cardProfile.setOnClickListener {
            startActivity(Intent(this, ProfileActivity::class.java))
        }

        binding.btnContinueReading.setOnClickListener {
            Toast.makeText(this, "Скоро здесь будет чтение книг", Toast.LENGTH_SHORT).show()
        }

        binding.btnMyBooks.setOnClickListener {
            startActivity(Intent(this, MyBooksActivity::class.java))
        }

        binding.btnStats.setOnClickListener {
            Toast.makeText(this, "Скоро здесь будет статистика", Toast.LENGTH_SHORT).show()
        }

        loadUserStats()
        loadRequestsCount()
        startPeriodicRequestsCheck()
    }

    private fun loadUserStats() {
        api.getUserStats("Token $token").enqueue(object : Callback<UserStatsResponse> {
            override fun onResponse(call: Call<UserStatsResponse>, response: Response<UserStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    binding.tvBooksCount.text = stats.books_count.toString()
                    binding.tvPagesCount.text = stats.total_pages.toString()
                }
            }

            override fun onFailure(call: Call<UserStatsResponse>, t: Throwable) {
                // Не показываем ошибку
            }
        })
    }

    private fun loadRequestsCount() {
        api.getRequestsCount("Token $token").enqueue(object : Callback<RequestsCountResponse> {
            override fun onResponse(call: Call<RequestsCountResponse>, response: Response<RequestsCountResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val count = response.body()!!.total
                    if (count > 0) {
                        binding.badgeRequests.visibility = android.view.View.VISIBLE
                    } else {
                        binding.badgeRequests.visibility = android.view.View.GONE
                    }
                }
            }

            override fun onFailure(call: Call<RequestsCountResponse>, t: Throwable) {
                // Не показываем ошибку
            }
        })
    }

    private fun startPeriodicRequestsCheck() {
        requestsCountRunnable = object : Runnable {
            override fun run() {
                loadRequestsCount()
                handler.postDelayed(this, 30000)
            }
        }
        handler.post(requestsCountRunnable!!)
    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacks(requestsCountRunnable!!)
    }

    override fun onResume() {
        super.onResume()
        loadUserStats()
        loadRequestsCount()
    }
}