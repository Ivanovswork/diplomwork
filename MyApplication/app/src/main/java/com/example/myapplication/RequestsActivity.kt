package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityRequestsBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class RequestsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRequestsBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String

    private var friendRequests = mutableListOf<UserConnection>()
    private var parentRequests = mutableListOf<UserConnection>()
    private var unlinkRequests = mutableListOf<UnlinkRequestItem>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRequestsBinding.inflate(layoutInflater)
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

        loadAllRequests()
    }

    private fun loadAllRequests() {
        api.getFriendRequests("Token $token").enqueue(object : Callback<FriendRequestsResponse> {
            override fun onResponse(call: Call<FriendRequestsResponse>, response: Response<FriendRequestsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    friendRequests = response.body()!!.friend_requests.toMutableList()
                    updateUI()
                }
            }
            override fun onFailure(call: Call<FriendRequestsResponse>, t: Throwable) {}
        })

        api.getParentRequests("Token $token").enqueue(object : Callback<ParentRequestsResponse> {
            override fun onResponse(call: Call<ParentRequestsResponse>, response: Response<ParentRequestsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    parentRequests = response.body()!!.parent_requests.toMutableList()
                    updateUI()
                }
            }
            override fun onFailure(call: Call<ParentRequestsResponse>, t: Throwable) {}
        })

        api.getUnlinkRequests("Token $token").enqueue(object : Callback<UnlinkRequestResponse> {
            override fun onResponse(call: Call<UnlinkRequestResponse>, response: Response<UnlinkRequestResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    unlinkRequests = response.body()!!.unlink_requests.toMutableList()
                    updateUI()
                }
            }
            override fun onFailure(call: Call<UnlinkRequestResponse>, t: Throwable) {}
        })
    }

    private fun updateUI() {
        binding.tvFriendRequestsCount.text = "${friendRequests.size}"
        binding.tvParentRequestsCount.text = "${parentRequests.size}"
        binding.tvUnlinkRequestsCount.text = "${unlinkRequests.size}"

        setupFriendRequests()
        setupParentRequests()
        setupUnlinkRequests()

        if (friendRequests.isEmpty() && parentRequests.isEmpty() && unlinkRequests.isEmpty()) {
            binding.tvEmpty.visibility = android.view.View.VISIBLE
        } else {
            binding.tvEmpty.visibility = android.view.View.GONE
        }
    }

    private fun setupFriendRequests() {
        binding.rvFriendRequests.layoutManager = LinearLayoutManager(this)
        binding.rvFriendRequests.adapter = FriendRequestsAdapter(friendRequests)
    }

    private fun setupParentRequests() {
        binding.rvParentRequests.layoutManager = LinearLayoutManager(this)
        binding.rvParentRequests.adapter = ParentRequestsAdapter(parentRequests)
    }

    private fun setupUnlinkRequests() {
        binding.rvUnlinkRequests.layoutManager = LinearLayoutManager(this)
        binding.rvUnlinkRequests.adapter = UnlinkRequestsAdapter(unlinkRequests)
    }

    private fun confirmFriend(request: UserConnection) {
        val req = ConnectionRequest(request.user1_data.id)
        api.confirmFriendRequest("Token $token", req).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Друг добавлен", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                } else {
                    Toast.makeText(this@RequestsActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }
            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {}
        })
    }

    private fun rejectFriend(request: UserConnection) {
        val req = ConnectionRequest(request.user1_data.id)
        api.rejectFriendRequest("Token $token", req).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Запрос отклонен", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                }
            }
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {}
        })
    }

    private fun confirmParent(request: UserConnection) {
        val req = mapOf("target_parent_id" to request.user1_data.id)
        api.confirmParentConnection("Token $token", req).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Родитель добавлен", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                }
            }
            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {}
        })
    }

    private fun rejectParent(request: UserConnection) {
        val req = ConnectionRequest(request.user1_data.id)
        api.rejectParentConnection("Token $token", req).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Запрос отклонен", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                }
            }
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {}
        })
    }

    private fun confirmUnlink(request: UnlinkRequestItem) {
        val req = mapOf("connection_id" to request.id)
        api.confirmUnlink("Token $token", req).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Связь удалена", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                }
            }
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {}
        })
    }

    private fun rejectUnlink(request: UnlinkRequestItem) {
        val req = mapOf("connection_id" to request.id)
        api.rejectUnlink("Token $token", req).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@RequestsActivity, "Отвязка отклонена", Toast.LENGTH_SHORT).show()
                    loadAllRequests()
                }
            }
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {}
        })
    }

    inner class FriendRequestsAdapter(
        private val requests: List<UserConnection>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<FriendRequestsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemRequestBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val req = requests[position]
            holder.binding.tvName.text = req.user1_data.name
            holder.binding.tvEmail.text = req.user1_data.email
            holder.binding.btnAccept.setOnClickListener { confirmFriend(req) }
            holder.binding.btnReject.setOnClickListener { rejectFriend(req) }
        }

        override fun getItemCount() = requests.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemRequestBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }

    inner class ParentRequestsAdapter(
        private val requests: List<UserConnection>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<ParentRequestsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemParentRequestBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val req = requests[position]
            holder.binding.tvName.text = req.user1_data.name
            holder.binding.tvEmail.text = req.user1_data.email
            holder.binding.btnAccept.setOnClickListener { confirmParent(req) }
            holder.binding.btnReject.setOnClickListener { rejectParent(req) }
        }

        override fun getItemCount() = requests.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemParentRequestBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }

    inner class UnlinkRequestsAdapter(
        private val requests: List<UnlinkRequestItem>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<UnlinkRequestsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemUnlinkRequestBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val req = requests[position]
            holder.binding.tvName.text = req.child_name
            holder.binding.tvEmail.text = req.child_email
            holder.binding.btnAccept.setOnClickListener { confirmUnlink(req) }
            holder.binding.btnReject.setOnClickListener { rejectUnlink(req) }
        }

        override fun getItemCount() = requests.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemUnlinkRequestBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}