package com.example.myapplication

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.*


// ==================== МОДЕЛИ ДАННЫХ ====================

// Аутентификация
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


// Общие связи
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


// Друзья
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


// Родительский контроль
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


// Запросы на отвязку
data class UnlinkRequestItem(
    val id: Int,
    val child_id: Int,
    val child_name: String,
    val child_email: String
)

data class UnlinkRequestResponse(
    val unlink_requests: List<UnlinkRequestItem>
)


// Запросы и уведомления
data class RequestsCountResponse(
    val total: Int,
    val friend_requests: Int,
    val parent_requests: Int,
    val unlink_requests: Int
)


// Статистика пользователя
data class UserStatsResponse(
    val books_count: Int,
    val total_pages: Int
)


// Книги
data class Book(
    val id: Int,
    val name: String,
    val pages_count: Int,
    val status: String,
    val daily_goal: Int,
    val upload_date: String,
    val is_owner: Boolean,
    val can_delete: Boolean,
    val uploaded_by_name: String?,
    val uploaded_by_id: Int?
)

data class BooksResponse(
    val my_books: List<Book>,
    val count: Int
)

data class ChildBooksResponse(
    val child_books: List<Book>,
    val count: Int
)

data class BookDetailsResponse(
    val id: Int,
    val name: String,
    val pages_count: Int,
    val daily_goal: Int,
    val status: String,
    val upload_date: String,
    val is_owner: Boolean
)

data class UpdateDailyGoalRequest(
    val daily_goal: Int
)

data class CheckBookLimitResponse(
    val can_upload: Boolean,
    val current_count: Int,
    val limit: Int,
    val message: String
)


// Чтение - Статистика книги
data class BookStatsResponse(
    val book_id: Int,
    val book_name: String,
    val total_pages: Int,
    val pages_read: Int,
    val progress_percent: Double,
    val total_time_seconds: Double,
    val total_time_formatted: String,
    val avg_time_per_page_seconds: Double,
    val total_words: Int,
    val reading_speed_wpm: Double,
    val total_sessions: Int,
    val has_active_session: Boolean,
    val active_session_id: Int?,
    val last_page_read: Int,
    val daily_goal: Int,
    val pages_read_today: Int,
    val daily_goal_achieved: Boolean,
    val daily_goal_percent: Int,
    val daily_goal_remaining: Int
)

// Чтение - Сессия
data class SessionResponse(
    val session_id: Int,
    val start_page: Int,
    val current_page: Int,
    val total_pages: Int,
    val is_book_finished: Boolean? = false
)

data class SessionProgressResponse(
    val session_id: Int,
    val start_page: Int,
    val end_page: Int?,
    val pages_read: Int,
    val status: String,
    val current_page: Int,
    val total_pages: Int,
    val is_active: Boolean,
    val is_completed: Boolean
)

// Чтение - Сохранение страницы
data class SavePageRequest(
    val session_id: Int,
    val page_number: Int,
    val time_spent: Int,
    val words_count: Int
)

data class SavePageResponse(
    val success: Boolean,
    val page_saved: Int,
    val is_book_finished: Boolean,
    val pages_read_in_session: Int,
    val total_pages: Int,
    val remaining_pages: Int,
    val daily_goal_completed: Boolean = false,
    val pages_read_today: Int = 0,
    val daily_goal: Int = 0,
    val test_created: Boolean = false,      // ← новое поле
    val test_id: Int? = null                // ← новое поле
)

// Чтение - Стрик
data class StreakResponse(
    val current_streak: Int,
    val longest_streak: Int,
    val last_read_date: String?
)

// Чтение - Общая статистика
data class ReadingStatsResponse(
    val total_pages: Int,
    val total_time_seconds: Double,
    val total_time_formatted: String,
    val total_words: Int,
    val reading_speed_wpm: Double,
    val books_in_progress: Int,
    val books_completed: Int,
    val total_sessions: Int,
    val avg_session_duration_seconds: Double
)

// Модели для тестов
data class TestResponse(
    val test_id: Int,
    val status: String,
    val start_page: Int,
    val end_page: Int,
    val questions: List<TestQuestion>,
    val score: Int,
    val total: Int
)

data class TestQuestion(
    val id: Int,
    val text: String,
    val answers: List<TestAnswer>
)

data class TestAnswer(
    val id: Int,
    val text: String
)

data class SubmitTestRequest(
    val answers: Map<String, Int>
)

data class SubmitTestResponse(
    val correct: Int,
    val total: Int,
    val passed: Boolean,
    val message: String
)

data class CheckTestResponse(
    val requires_test: Boolean,
    val test_id: Int? = null,
    val message: String? = null,
    val start_page: Int? = null,
    val end_page: Int? = null,
    val retake: Boolean = false
)

data class BookTestStatsResponse(
    val total_tests: Int,
    val average_score: Double,
    val passed_tests: Int,
    val results: List<TestResult>
)

data class TestResult(
    val id: Int,
    val test_id: Int,
    val correct_answers: Int,
    val total_questions: Int,
    val score_percent: Int,
    val completed_at: String,
    val start_page: Int,
    val end_page: Int
)

data class RefreshStatsResponse(
    val book_id: Int,
    val book_name: String,
    val total_pages: Int,
    val pages_read: Int,
    val progress_percent: Double,
    val daily_goal: Int,
    val pages_read_today: Int,
    val daily_goal_achieved: Boolean,
    val daily_goal_percent: Int,
    val daily_goal_remaining: Int
)
// ==================== ИНТЕРФЕЙС API ====================

interface DjangoApi {

    // ==================== АУТЕНТИФИКАЦИЯ ====================

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


    // ==================== ДРУЗЬЯ ====================

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


    // ==================== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ====================

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


    // ==================== ЗАПРОСЫ НА ОТВЯЗКУ ====================

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


    // ==================== ЗАПРОСЫ И УВЕДОМЛЕНИЯ ====================

    @GET("api/books/connections/requests-count/")
    fun getRequestsCount(@Header("Authorization") token: String): Call<RequestsCountResponse>

    @GET("api/books/connections/")
    fun getMyConnections(@Header("Authorization") token: String): Call<ConnectionsResponse>


    // ==================== СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ ====================

    @GET("api/books/stats/")
    fun getUserStats(@Header("Authorization") token: String): Call<UserStatsResponse>


    // ==================== КНИГИ ====================

    @GET("api/books/books/my/")
    fun getMyBooks(@Header("Authorization") token: String): Call<BooksResponse>

    @GET("api/books/books/child/{childId}/")
    fun getChildBooks(
        @Header("Authorization") token: String,
        @Path("childId") childId: Int
    ): Call<ChildBooksResponse>

    @Multipart
    @POST("api/books/books/")
    fun uploadBook(
        @Header("Authorization") token: String,
        @Part("name") name: RequestBody,
        @Part("daily_goal") dailyGoal: RequestBody,
        @Part file: MultipartBody.Part
    ): Call<Map<String, Any>>

    @Multipart
    @POST("api/books/books/child/")
    fun uploadBookToChild(
        @Header("Authorization") token: String,
        @Part("child_id") childId: RequestBody,
        @Part("name") name: RequestBody,
        @Part("daily_goal") dailyGoal: RequestBody,
        @Part file: MultipartBody.Part
    ): Call<Map<String, Any>>

    @GET("api/books/books/{bookId}/")
    fun getBookDetails(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<BookDetailsResponse>

    @PUT("api/books/books/{bookId}/daily-goal/")
    fun updateDailyGoal(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int,
        @Body body: UpdateDailyGoalRequest
    ): Call<Map<String, Any>>

    @DELETE("api/books/books/{bookId}/delete/")
    fun deleteBook(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<Map<String, String>>

    @GET("api/books/books/limit/")
    fun getBookLimit(@Header("Authorization") token: String): Call<CheckBookLimitResponse>

    @GET("api/books/books/child-limit/{childId}/")
    fun getChildBookLimit(
        @Header("Authorization") token: String,
        @Path("childId") childId: Int
    ): Call<CheckBookLimitResponse>


    // ==================== ЧТЕНИЕ ====================

    // Статистика книги
    @GET("api/reading/book/{bookId}/stats/")
    fun getBookStats(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<BookStatsResponse>

    @GET("api/reading/book/{bookId}/refresh-stats/")
    fun refreshBookStats(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<RefreshStatsResponse>

    // Сессии
    @GET("api/reading/session/{bookId}/")
    fun getOrCreateSession(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<SessionResponse>

    @GET("api/reading/session/progress/{sessionId}/")
    fun getSessionProgress(
        @Header("Authorization") token: String,
        @Path("sessionId") sessionId: Int
    ): Call<SessionProgressResponse>

    @POST("api/reading/session/{sessionId}/continue/")
    fun continueReading(
        @Header("Authorization") token: String,
        @Path("sessionId") sessionId: Int
    ): Call<SessionResponse>

    @POST("api/reading/session/{sessionId}/finish/")
    fun finishReading(
        @Header("Authorization") token: String,
        @Path("sessionId") sessionId: Int
    ): Call<Map<String, Boolean>>

    // Страницы
    @POST("api/reading/page/save/")
    fun savePageRead(
        @Header("Authorization") token: String,
        @Body body: SavePageRequest
    ): Call<SavePageResponse>

    @GET("api/reading/pdf-proxy/{bookId}/")
    fun getPage(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int,
        @Query("page") page: Int
    ): Call<ResponseBody>

    // Стрик и общая статистика
    @GET("api/reading/streak/")
    fun getUserStreak(@Header("Authorization") token: String): Call<StreakResponse>

    @GET("api/reading/stats/")
    fun getReadingStats(@Header("Authorization") token: String): Call<ReadingStatsResponse>

    // Добавь в интерфейс DjangoApi
    @GET("api/reading/test/{testId}/")
    fun getTest(
        @Header("Authorization") token: String,
        @Path("testId") testId: Int
    ): Call<TestResponse>

    @POST("api/reading/test/{testId}/submit/")
    fun submitTest(
        @Header("Authorization") token: String,
        @Path("testId") testId: Int,
        @Body body: SubmitTestRequest
    ): Call<SubmitTestResponse>

    @GET("api/reading/test/check/{sessionId}/")
    fun checkTestRequired(
        @Header("Authorization") token: String,
        @Path("sessionId") sessionId: Int
    ): Call<CheckTestResponse>

    @POST("api/reading/test/{testId}/retake/")
    fun retakeTest(
        @Header("Authorization") token: String,
        @Path("testId") testId: Int
    ): Call<Map<String, Any>>

    @GET("api/reading/book/{bookId}/test-stats/")
    fun getBookTestStats(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<BookTestStatsResponse>

    @GET("api/reading/book/{bookId}/stats/")
    fun getBookStatsWithDaily(
        @Header("Authorization") token: String,
        @Path("bookId") bookId: Int
    ): Call<BookStatsResponse>
}