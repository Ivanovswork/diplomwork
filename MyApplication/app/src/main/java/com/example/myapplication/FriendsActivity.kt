package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityFriendsBinding
import com.example.myapplication.databinding.ItemUserBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class FriendsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityFriendsBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var friendsList = mutableListOf<Friend>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityFriendsBinding.inflate(layoutInflater)
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

        binding.btnAddFriend.setOnClickListener {
            val email = binding.etUserEmail.text.toString().trim()
            if (email.isEmpty()) {
                Toast.makeText(this, "Введите email пользователя", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            addFriendByEmail(email)
        }

        loadFriends()
    }

    private fun loadFriends() {
        api.listFriends("Token $token").enqueue(object : Callback<FriendsListResponse> {
            override fun onResponse(call: Call<FriendsListResponse>, response: Response<FriendsListResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    friendsList = response.body()!!.friends.toMutableList()
                    setupRecyclerView()
                    if (friendsList.isEmpty()) {
                        binding.tvEmpty.visibility = android.view.View.VISIBLE
                    } else {
                        binding.tvEmpty.visibility = android.view.View.GONE
                    }
                }
            }

            override fun onFailure(call: Call<FriendsListResponse>, t: Throwable) {
                Toast.makeText(this@FriendsActivity, "Ошибка загрузки: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun setupRecyclerView() {
        binding.rvFriends.layoutManager = LinearLayoutManager(this)
        binding.rvFriends.adapter = FriendsAdapter(friendsList)
    }

    private fun addFriendByEmail(email: String) {
        val request = AddByEmailRequest(email)
        api.addFriendByEmail("Token $token", request).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@FriendsActivity, "Запрос отправлен", Toast.LENGTH_SHORT).show()
                    binding.etUserEmail.text?.clear()
                    loadFriends()
                } else {
                    when (response.code()) {
                        404 -> Toast.makeText(this@FriendsActivity, "Пользователь не найден", Toast.LENGTH_SHORT).show()
                        400 -> Toast.makeText(this@FriendsActivity, "Уже друзья или запрос отправлен", Toast.LENGTH_SHORT).show()
                        else -> Toast.makeText(this@FriendsActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@FriendsActivity, "Сеть недоступна", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun removeFriend(friend: Friend) {
        val request = ConnectionRequest(friend.id)
        api.removeFriend("Token $token", request).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@FriendsActivity, "Друг удален", Toast.LENGTH_SHORT).show()
                    loadFriends()
                }
            }

            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                Toast.makeText(this@FriendsActivity, "Ошибка", Toast.LENGTH_SHORT).show()
            }
        })
    }

    inner class FriendsAdapter(
        private val friends: List<Friend>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<FriendsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = ItemUserBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val friend = friends[position]
            holder.binding.tvName.text = "${friend.name} (${friend.email})"
            holder.binding.btnRemove.setOnClickListener {
                removeFriend(friend)
            }
        }

        override fun getItemCount() = friends.size

        inner class ViewHolder(val binding: ItemUserBinding) : androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}