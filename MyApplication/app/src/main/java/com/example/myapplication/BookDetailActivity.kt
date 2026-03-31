package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityBookDetailBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class BookDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityBookDetailBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var bookId: Int = 0
    private var bookName: String = ""
    private var readOnly: Boolean = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityBookDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        bookId = intent.getIntExtra("book_id", 0)
        bookName = intent.getStringExtra("book_name") ?: "Книга"
        readOnly = intent.getBooleanExtra("read_only", false)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.btnBack.setOnClickListener { finish() }

        if (readOnly) {
            binding.btnRead.visibility = android.view.View.GONE
        } else {
            binding.btnRead.visibility = android.view.View.VISIBLE
            binding.btnRead.setOnClickListener { startReading() }
        }

        loadBookStats()
    }

    override fun onResume() {
        super.onResume()
        if (bookId != 0) {
            loadBookStats()
        }
    }

    private fun loadBookStats() {
        api.getBookStatsWithDaily("Token $token", bookId).enqueue(object : Callback<BookStatsResponse> {
            override fun onResponse(call: Call<BookStatsResponse>, response: Response<BookStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    updateUI(stats)
                } else {
                    Toast.makeText(this@BookDetailActivity, "Ошибка загрузки статистики: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<BookStatsResponse>, t: Throwable) {
                Toast.makeText(this@BookDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun updateUI(stats: BookStatsResponse) {
        binding.tvPagesRead.text = "${stats.pages_read} / ${stats.total_pages}"
        binding.progressBar.progress = stats.progress_percent.toInt()
        binding.tvProgressPercent.text = "${stats.progress_percent.toInt()}%"
        binding.tvTotalTime.text = formatTime(stats.total_time_seconds)
        binding.tvAvgTimePerPage.text = formatTime(stats.avg_time_per_page_seconds)
        binding.tvTotalWords.text = stats.total_words.toString()
        binding.tvReadingSpeed.text = "${stats.reading_speed_wpm.toInt()} слов/мин"
        binding.tvTotalSessions.text = stats.total_sessions.toString()

        // Дневная цель
        binding.tvDailyGoal.text = "${stats.pages_read_today} / ${stats.daily_goal} стр."
        binding.tvDailyGoalRemaining.text = "Осталось: ${stats.daily_goal_remaining} стр."

        if (stats.daily_goal_achieved) {
            binding.tvDailyGoal.setTextColor(resources.getColor(android.R.color.holo_green_dark, null))
            binding.tvDailyGoalRemaining.visibility = android.view.View.GONE
        } else {
            binding.tvDailyGoal.setTextColor(resources.getColor(android.R.color.white, null))
            binding.tvDailyGoalRemaining.visibility = android.view.View.VISIBLE
        }

        if (stats.has_active_session) {
            binding.btnRead.text = "Продолжить чтение"
        } else {
            binding.btnRead.text = "Начать чтение"
        }
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

    private fun startReading() {
        val intent = Intent(this, ReadingActivity::class.java)
        intent.putExtra("book_id", bookId)
        intent.putExtra("book_name", bookName)
        startActivity(intent)
    }
}