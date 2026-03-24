package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.ImageButton
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.cardview.widget.CardView

class ProfileActivity : AppCompatActivity() {

    private lateinit var api: DjangoApi
    private lateinit var token: String

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)

        val btnBack = findViewById<ImageButton>(R.id.btnBack)
        val tvUserName = findViewById<TextView>(R.id.tvUserName)
        val tvUserEmail = findViewById<TextView>(R.id.tvUserEmail)

        val cardFriends = findViewById<CardView>(R.id.cardFriends)
        val cardParentControl = findViewById<CardView>(R.id.cardParentControl)
        val cardRequests = findViewById<CardView>(R.id.cardRequests)
        val cardChangePassword = findViewById<CardView>(R.id.cardChangePassword)
        val cardLogout = findViewById<CardView>(R.id.cardLogout)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""
        val email = prefs.getString("email", "user@example.com")
        val userName = prefs.getString("user_name", "Читатель")

        tvUserName.text = userName
        tvUserEmail.text = email

        val retrofit = retrofit2.Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(retrofit2.converter.gson.GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        btnBack.setOnClickListener {
            finish()
        }

        cardFriends.setOnClickListener {
            startActivity(Intent(this, FriendsActivity::class.java))
        }

        cardParentControl.setOnClickListener {
            startActivity(Intent(this, ParentControlActivity::class.java))
        }

        cardRequests.setOnClickListener {
            startActivity(Intent(this, RequestsActivity::class.java))
        }

        cardChangePassword.setOnClickListener {
            startActivity(Intent(this, ChangePasswordActivity::class.java))
        }

        cardLogout.setOnClickListener {
            prefs.edit().clear().apply()
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
        }

        loadRequestsCount()
    }

    private fun loadRequestsCount() {
        api.getRequestsCount("Token $token").enqueue(object : retrofit2.Callback<RequestsCountResponse> {
            override fun onResponse(call: retrofit2.Call<RequestsCountResponse>, response: retrofit2.Response<RequestsCountResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val count = response.body()!!.total
                    val tvRequestsBadge = findViewById<TextView>(R.id.tvRequestsBadge)
                    if (count > 0) {
                        tvRequestsBadge.text = if (count > 99) "99+" else count.toString()
                        tvRequestsBadge.visibility = android.view.View.VISIBLE
                    } else {
                        tvRequestsBadge.visibility = android.view.View.GONE
                    }
                }
            }

            override fun onFailure(call: retrofit2.Call<RequestsCountResponse>, t: Throwable) {}
        })
    }

    override fun onResume() {
        super.onResume()
        loadRequestsCount()
    }
}