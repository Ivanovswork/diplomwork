package com.example.myapplication

import retrofit2.Call
import retrofit2.http.*

// ==================== АУТЕНТИФИКАЦИЯ ====================

data class RegisterRequest(
    val name: String,
    val email: String,
    val password: String,
    val password_confirm: String
)

data class RegisterResponse(
    val status: String? = null,
    val errors: Any? = null
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val user: User? = null
)

data class User(
    val id: Int,
    val name: String,
    val email: String,
    val is_account_active: Boolean,
    val subscription_type: String
)

data class ChangePasswordRequest(
    val old_password: String,
    val new_password: String,
    val new_password_confirm: String
)

data class ChangePasswordResponse(
    val status: String
)


// ==================== ОБЩИЕ СВЯЗИ ====================

data class ConnectionRequest(
    val target_user_id: Int? = null,
    val email: String? = null
)

data class UserConnection(
    val id: Int,
    val user1_data: User,
    val user2_data: User,
    val connection_type: String,
    val is_parent_flag: Boolean,
    val is_child_flag: Boolean,
    val status: String
)

data class ConnectionsResponse(
    val my_connections: List<UserConnection>,
    val total: Int,
    val active: Int
)


// ==================== ДРУЗЬЯ ====================

data class Friend(
    val id: Int,
    val name: String,
    val email: String,
    val connection_id: Int
)

data class FriendsListResponse(
    val friends: List<Friend>
)

data class FriendRequestsResponse(
    val friend_requests: List<UserConnection>,
    val pending_count: Int
)


// ==================== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ====================

data class Child(
    val id: Int,
    val name: String,
    val email: String,
    val connection_id: Int
)

data class ChildrenListResponse(
    val children: List<Child>
)

data class Parent(
    val id: Int,
    val name: String,
    val email: String,
    val connection_id: Int
)

data class ParentsListResponse(
    val parents: List<Parent>
)

data class ParentRequestsResponse(
    val parent_requests: List<UserConnection>,
    val pending_count: Int
)

data class AddByEmailRequest(
    val email: String
)


// ==================== ЗАПРОСЫ НА ОТВЯЗКУ ====================

data class UnlinkRequestItem(
    val id: Int,
    val child_id: Int,
    val child_name: String,
    val child_email: String
)

data class UnlinkRequestResponse(
    val unlink_requests: List<UnlinkRequestItem>
)


// ==================== ЗАПРОСЫ И УВЕДОМЛЕНИЯ ====================

data class RequestsCountResponse(
    val total: Int,
    val friend_requests: Int,
    val parent_requests: Int,
    val unlink_requests: Int
)


// ==================== ИНТЕРФЕЙС API ====================

interface DjangoApi {

    // ========== АУТЕНТИФИКАЦИЯ ==========

    @POST("api/users/register/")
    fun register(@Body body: RegisterRequest): Call<RegisterResponse>

    @POST("api/users/login/")
    fun login(@Body body: LoginRequest): Call<LoginResponse>

    @PUT("api/users/change-password/")
    fun changePassword(
        @Header("Authorization") token: String,
        @Body body: ChangePasswordRequest
    ): Call<ChangePasswordResponse>

    @POST("api/users/logout/")
    fun logout(@Header("Authorization") token: String): Call<Map<String, String>>


    // ========== ДРУЗЬЯ ==========

    @GET("api/books/friends/")
    fun listFriends(@Header("Authorization") token: String): Call<FriendsListResponse>

    @GET("api/books/friends/requests/")
    fun getFriendRequests(@Header("Authorization") token: String): Call<FriendRequestsResponse>

    @POST("api/books/friends/add-by-email/")
    fun addFriendByEmail(
        @Header("Authorization") token: String,
        @Body body: AddByEmailRequest
    ): Call<Map<String, Any>>

    @POST("api/books/friends/request/")
    fun sendFriendRequest(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, Any>>

    @POST("api/books/friends/confirm/")
    fun confirmFriendRequest(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, Any>>

    @POST("api/books/friends/reject/")
    fun rejectFriendRequest(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, String>>

    @POST("api/books/friends/remove/")
    fun removeFriend(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, String>>


    // ========== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ==========

    @GET("api/books/parent/children/")
    fun listChildren(@Header("Authorization") token: String): Call<ChildrenListResponse>

    @GET("api/books/parent/parents/")
    fun listParents(@Header("Authorization") token: String): Call<ParentsListResponse>

    @POST("api/books/parent/request-by-email/")
    fun requestParentByEmail(
        @Header("Authorization") token: String,
        @Body body: AddByEmailRequest
    ): Call<Map<String, Any>>

    @GET("api/books/connections/parent-requests/")
    fun getParentRequests(@Header("Authorization") token: String): Call<ParentRequestsResponse>

    @POST("api/books/connections/request/")
    fun sendParentRequest(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, Any>>

    @POST("api/books/connections/confirm/")
    fun confirmParentConnection(
        @Header("Authorization") token: String,
        @Body body: Map<String, Int>
    ): Call<Map<String, Any>>

    @POST("api/books/connections/reject/")
    fun rejectParentConnection(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, String>>

    @POST("api/books/connections/unlink-child/")
    fun unlinkByChild(
        @Header("Authorization") token: String,
        @Body body: Map<String, Int>
    ): Call<Map<String, Any>>

    @POST("api/books/connections/unlink-parent/")
    fun unlinkByParent(
        @Header("Authorization") token: String,
        @Body body: ConnectionRequest
    ): Call<Map<String, String>>


    // ========== ЗАПРОСЫ НА ОТВЯЗКУ ==========

    @GET("api/books/connections/unlink-requests/")
    fun getUnlinkRequests(@Header("Authorization") token: String): Call<UnlinkRequestResponse>

    @POST("api/books/connections/confirm-unlink/")
    fun confirmUnlink(
        @Header("Authorization") token: String,
        @Body body: Map<String, Int>
    ): Call<Map<String, String>>

    @POST("api/books/connections/reject-unlink/")
    fun rejectUnlink(
        @Header("Authorization") token: String,
        @Body body: Map<String, Int>
    ): Call<Map<String, String>>


    // ========== ЗАПРОСЫ И УВЕДОМЛЕНИЯ ==========

    @GET("api/books/connections/requests-count/")
    fun getRequestsCount(@Header("Authorization") token: String): Call<RequestsCountResponse>

    @GET("api/books/connections/")
    fun getMyConnections(@Header("Authorization") token: String): Call<ConnectionsResponse>
}