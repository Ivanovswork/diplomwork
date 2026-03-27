package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityReadingStatsBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ReadingStatsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityReadingStatsBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityReadingStatsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.btnBack.setOnClickListener {
            finish()
        }

        loadStats()
    }

    private fun loadStats() {
        api.getReadingStats("Token $token").enqueue(object : Callback<ReadingStatsResponse> {
            override fun onResponse(call: Call<ReadingStatsResponse>, response: Response<ReadingStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    binding.tvTotalPages.text = stats.total_pages.toString()
                    binding.tvTotalTime.text = formatTime(stats.total_time_seconds)
                    binding.tvTotalWords.text = stats.total_words.toString()
                    binding.tvReadingSpeed.text = "${stats.reading_speed_wpm.toInt()} слов/мин"
                    binding.tvBooksInProgress.text = stats.books_in_progress.toString()
                    binding.tvBooksCompleted.text = stats.books_completed.toString()
                    binding.tvTotalSessions.text = stats.total_sessions.toString()
                    binding.tvAvgSessionDuration.text = formatTime(stats.avg_session_duration_seconds)
                } else {
                    Toast.makeText(this@ReadingStatsActivity, "Ошибка загрузки статистики", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<ReadingStatsResponse>, t: Throwable) {
                Toast.makeText(this@ReadingStatsActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun formatTime(seconds: Double): String {
        val secs = seconds.toInt()
        val minutes = secs / 60
        val remainingSecs = secs % 60
        return if (minutes > 0) {
            "${minutes}м ${remainingSecs}с"
        } else {
            "${secs}с"
        }
    }
}