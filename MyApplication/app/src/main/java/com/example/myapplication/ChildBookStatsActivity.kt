package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityChildBookStatsBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ChildBookStatsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityChildBookStatsBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var childId: Int = 0
    private var childName: String = ""
    private var bookId: Int = 0
    private var bookName: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChildBookStatsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        childId = intent.getIntExtra("child_id", 0)
        childName = intent.getStringExtra("child_name") ?: ""
        bookId = intent.getIntExtra("book_id", 0)
        bookName = intent.getStringExtra("book_name") ?: ""

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.tvChildName.text = childName
        binding.btnBack.setOnClickListener { finish() }

        loadStats()
    }

    private fun loadStats() {
        api.getChildBookStats("Token $token", childId, bookId).enqueue(object : Callback<ChildBookStatsResponse> {
            override fun onResponse(call: Call<ChildBookStatsResponse>, response: Response<ChildBookStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    updateUI(stats)
                }
            }
            override fun onFailure(call: Call<ChildBookStatsResponse>, t: Throwable) {
                Toast.makeText(this@ChildBookStatsActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun updateUI(stats: ChildBookStatsResponse) {
        // Прогресс чтения
        binding.tvPagesRead.text = "${stats.pages_read} / ${stats.total_pages}"
        binding.progressBar.progress = stats.progress_percent.toInt()
        binding.tvProgressPercent.text = "${stats.progress_percent.toInt()}%"

        // Время и скорость
        binding.tvTotalTime.text = stats.total_time_formatted
        binding.tvAvgTimePerPage.text = formatTime(stats.avg_time_per_page_seconds)
        binding.tvTotalWords.text = stats.total_words.toString()
        binding.tvReadingSpeed.text = "${stats.reading_speed_wpm.toInt()} слов/мин"
        binding.tvTotalSessions.text = stats.total_sessions.toString()

        // Тесты
        if (stats.total_tests > 0) {
            binding.testStatsContainer.visibility = android.view.View.VISIBLE
            binding.tvTotalTests.text = stats.total_tests.toString()
            binding.tvPassedTests.text = "${stats.passed_tests} / ${stats.total_tests}"
            binding.tvAvgTestScore.text = "${stats.avg_test_score_percent.toInt()}%"

            binding.rvTestResults.layoutManager = LinearLayoutManager(this)
            binding.rvTestResults.adapter = TestResultsAdapter(stats.test_results)
        }
    }

    private fun formatTime(seconds: Double): String {
        val secs = seconds.toInt()
        val minutes = secs / 60
        val remainingSecs = secs % 60
        return if (minutes > 0) "${minutes}м ${remainingSecs}с" else "${secs}с"
    }

    inner class TestResultsAdapter(private val results: List<ChildTestResult>) :
        androidx.recyclerview.widget.RecyclerView.Adapter<TestResultsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemTestResultBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val result = results[position]
            holder.binding.tvPagesRange.text = "Страницы ${result.start_page}-${result.end_page}"
            holder.binding.tvScore.text = "${result.correct_answers} / ${result.total_questions}"
            holder.binding.tvScorePercent.text = "${result.score_percent}%"

            val color = when {
                result.score_percent >= 67 -> android.R.color.holo_green_dark
                result.score_percent >= 34 -> android.R.color.holo_orange_dark
                else -> android.R.color.holo_red_dark
            }
            holder.binding.tvScorePercent.setTextColor(resources.getColor(color, null))

            try {
                val date = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.getDefault())
                    .parse(result.completed_at)
                val formattedDate = java.text.SimpleDateFormat("dd.MM.yyyy HH:mm", java.util.Locale.getDefault())
                    .format(date)
                holder.binding.tvDate.text = formattedDate
            } catch (e: Exception) {
                holder.binding.tvDate.text = result.completed_at.substring(0, 10)
            }
        }

        override fun getItemCount() = results.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemTestResultBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}