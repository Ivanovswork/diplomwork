package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.myapplication.databinding.ActivityHomeBinding
import com.example.myapplication.databinding.ItemLeaderboardBinding
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
    private lateinit var leaderboardAdapter: LeaderboardAdapter
    private var leaderboardList = mutableListOf<LeaderboardUser>()

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

        binding.btnMyBooks.setOnClickListener {
            startActivity(Intent(this, MyBooksActivity::class.java))
        }

        binding.btnStats.setOnClickListener {
            startActivity(Intent(this, ReadingStatsActivity::class.java))
        }

        setupLeaderboard()
        loadUserStats()
        loadUserStreak()
        loadLeaderboard()
        loadRequestsCount()
        startPeriodicRequestsCheck()
    }

    private fun setupLeaderboard() {
        binding.rvLeaderboard.layoutManager = LinearLayoutManager(this)
        leaderboardAdapter = LeaderboardAdapter(leaderboardList)
        binding.rvLeaderboard.adapter = leaderboardAdapter
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
            override fun onFailure(call: Call<UserStatsResponse>, t: Throwable) {}
        })
    }

    private fun loadUserStreak() {
        api.getUserStreak("Token $token").enqueue(object : Callback<StreakResponse> {
            override fun onResponse(call: Call<StreakResponse>, response: Response<StreakResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val streak = response.body()!!
                    binding.tvStreakCount.text = streak.current_streak.toString()
                    binding.tvLongestStreak.text = streak.longest_streak.toString()
                }
            }
            override fun onFailure(call: Call<StreakResponse>, t: Throwable) {}
        })
    }

    private fun loadLeaderboard() {
        api.getLeaderboard("Token $token").enqueue(object : Callback<LeaderboardResponse> {
            override fun onResponse(call: Call<LeaderboardResponse>, response: Response<LeaderboardResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    leaderboardList.clear()
                    leaderboardList.addAll(response.body()!!.leaderboard)
                    leaderboardAdapter.notifyDataSetChanged()
                }
            }
            override fun onFailure(call: Call<LeaderboardResponse>, t: Throwable) {}
        })
    }

    private fun loadRequestsCount() {
        api.getRequestsCount("Token $token").enqueue(object : Callback<RequestsCountResponse> {
            override fun onResponse(call: Call<RequestsCountResponse>, response: Response<RequestsCountResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val count = response.body()!!.total
                    binding.badgeRequests.visibility = if (count > 0) View.VISIBLE else View.GONE
                }
            }
            override fun onFailure(call: Call<RequestsCountResponse>, t: Throwable) {}
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
        loadUserStreak()
        loadLeaderboard()
        loadRequestsCount()
    }

    inner class LeaderboardAdapter(
        private val users: List<LeaderboardUser>
    ) : RecyclerView.Adapter<LeaderboardAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = ItemLeaderboardBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val user = users[position]
            val rank = position + 1

            holder.binding.tvRank.text = rank.toString()
            holder.binding.tvName.text = if (user.is_current_user) "${user.name} (Вы)" else user.name
            holder.binding.tvStreak.text = user.current_streak.toString()
            holder.binding.tvPages.text = user.total_pages.toString()

            // Цвет имени для текущего пользователя
            if (user.is_current_user) {
                holder.binding.tvName.setTextColor(resources.getColor(R.color.primary_blue, null))
            } else {
                holder.binding.tvName.setTextColor(resources.getColor(R.color.text_dark, null))
            }

            // Медали для топ-3
            when (rank) {
                1 -> {
                    holder.binding.tvBadge.visibility = View.VISIBLE
                    holder.binding.tvBadge.text = "🥇"
                    holder.binding.tvRank.visibility = View.GONE
                }
                2 -> {
                    holder.binding.tvBadge.visibility = View.VISIBLE
                    holder.binding.tvBadge.text = "🥈"
                    holder.binding.tvRank.visibility = View.GONE
                }
                3 -> {
                    holder.binding.tvBadge.visibility = View.VISIBLE
                    holder.binding.tvBadge.text = "🥉"
                    holder.binding.tvRank.visibility = View.GONE
                }
                else -> {
                    holder.binding.tvBadge.visibility = View.GONE
                    holder.binding.tvRank.visibility = View.VISIBLE
                }
            }

            // Цвет стрика
            if (user.current_streak == 0) {
                holder.binding.tvStreak.setTextColor(resources.getColor(R.color.text_light, null))
            } else {
                holder.binding.tvStreak.setTextColor(resources.getColor(android.R.color.holo_orange_dark, null))
            }
        }

        override fun getItemCount() = users.size

        inner class ViewHolder(val binding: ItemLeaderboardBinding) : RecyclerView.ViewHolder(binding.root)
    }
}